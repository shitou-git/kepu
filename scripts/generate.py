#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主生成脚本 - 每日自动生成科普文章
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False

# 将 scripts 目录加入路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_rewrite import AIWriter
from image_search import ImageFinder


class MagazineGenerator:
    def __init__(self):
        with open("config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        self.writer = AIWriter()
        self.finder = ImageFinder()
        self.content_dir = Path("content/archives")
        self.content_dir.mkdir(parents=True, exist_ok=True)

    def get_today_themes(self, date: datetime = None, override_theme: str = "") -> list:
        """根据日期获取今日的2个主题"""
        if override_theme:
            for t in self.config["themes"]:
                if t["id"] == override_theme or t["name"] == override_theme:
                    return [t]
            print(f"警告: 未找到主题 '{override_theme}'，使用日期匹配")
        
        date = date or datetime.now()
        weekday = date.isoweekday()  # 1=周一, 7=周日
        
        matched = []
        for theme in self.config["themes"]:
            if weekday in theme["weekdays"]:
                matched.append(theme)
        
        # 如果匹配到多个，取前2个；如果不足2个，补充其他主题
        if len(matched) >= 2:
            return matched[:2]
        elif len(matched) == 1:
            # 补充一个不同的主题
            for t in self.config["themes"]:
                if t["id"] != matched[0]["id"]:
                    matched.append(t)
                    break
            return matched
        else:
            return self.config["themes"][:2]

    def generate_daily(self, override_theme: str = "", force_all: bool = False):
        """生成今日科普内容（每天4篇，分上午/下午两批）
        force_all: 强制生成今日所有主题，不受批次限制（手动触发时使用）
        """
        timezone = self.config["schedule"].get("timezone", "Asia/Shanghai")
        
        if HAS_ZONEINFO:
            today = datetime.now(ZoneInfo(timezone))
        else:
            today = datetime.now()
        
        date_str = today.strftime("%Y-%m-%d")
        current_hour = today.hour
        
        print(f"当前时间（{timezone}）: {today}")
        print(f"今日日期: {date_str}")
        
        if override_theme:
            target_theme = None
            for t in self.config["themes"]:
                if t["id"] == override_theme or t["name"] == override_theme:
                    target_theme = t
                    break
            if not target_theme:
                print(f"警告: 未找到主题 '{override_theme}'")
                return []
            return self._generate_for_theme(target_theme, date_str)
        
        date = today
        weekday = date.isoweekday()
        
        all_matched = []
        for theme in self.config["themes"]:
            if weekday in theme["weekdays"]:
                all_matched.append(theme)
        
        if len(all_matched) < 2:
            for t in self.config["themes"]:
                if t["id"] not in [m["id"] for m in all_matched]:
                    all_matched.append(t)
                    if len(all_matched) >= 4:
                        break
        
        all_matched = all_matched[:4]
        
        if force_all:
            batch_themes = all_matched
            print(f"手动触发，生成今日全部 {len(batch_themes)} 篇文章")
            print(f"今日主题: {[t['name'] for t in batch_themes]}")
        else:
            batch_size = 2
            if current_hour >= 16:
                batch_start = 2
                print("当前为下午批次（16:00后），生成第3-4篇")
            else:
                batch_start = 0
                print("当前为上午批次（16:00前），生成第1-2篇")
            
            batch_themes = all_matched[batch_start:batch_start + batch_size]
            print(f"本批次主题: {[t['name'] for t in batch_themes]}")
        
        existing_themes = set()
        for f in self.content_dir.glob(f"{date_str}*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("theme"):
                    existing_themes.add(data["theme"])
            except Exception:
                pass
        
        pending_themes = [t for t in batch_themes if t["id"] not in existing_themes]
        
        if not pending_themes:
            print(f"本批次 {len(batch_themes)} 篇文章均已生成，跳过")
            return []
        
        print(f"本批次待生成 {len(pending_themes)}/{len(batch_themes)} 篇文章")
        
        generated = []
        for idx, theme in enumerate(pending_themes):
            existing_count = len([f for f in self.content_dir.glob(f"{date_str}*.json")])
            file_date_str = f"{date_str}_{existing_count + 1}"
            
            article_file = self.content_dir / f"{file_date_str}.json"
            if article_file.exists():
                print(f"内容已存在，跳过: {article_file}")
                continue
            
            print(f"\n[{idx+1}/{len(pending_themes)}] 主题: {theme['name']} ({theme['id']})")
            
            try:
                # 生成文章
                print("正在生成文章...")
                article = self.writer.generate_article(theme["id"], theme["name"], date_str)
                article["date"] = date_str
                article["file_id"] = file_date_str
                
                # 搜索配图
                print("正在搜索配图...")
                image_prompts = article.get("image_prompts", [])
                image_paths = self.finder.search_images(
                    image_prompts,
                    count=len(image_prompts),
                    date_str=file_date_str
                )
                article["images"] = [Path(p).name for p in image_paths]
                
                # 保存文章数据
                article_file.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"文章已保存: {article_file}")
                
                # 更新索引
                self.update_index(article)
                generated.append(article)
            except Exception as e:
                print(f"生成失败，跳过: {e}")
                continue
        
        return generated
    
    def _generate_for_theme(self, theme, date_str):
        """为指定主题生成一篇文章"""
        existing_count = len([f for f in self.content_dir.glob(f"{date_str}*.json")])
        file_date_str = f"{date_str}_{existing_count + 1}"
        
        article_file = self.content_dir / f"{file_date_str}.json"
        if article_file.exists():
            print(f"内容已存在，跳过: {article_file}")
            return []
        
        print(f"\n生成主题: {theme['name']} ({theme['id']})")
        
        try:
            print("正在生成文章...")
            article = self.writer.generate_article(theme["id"], theme["name"], date_str)
            article["date"] = date_str
            article["file_id"] = file_date_str
            
            print("正在搜索配图...")
            image_prompts = article.get("image_prompts", [])
            image_paths = self.finder.search_images(
                image_prompts,
                count=len(image_prompts),
                date_str=file_date_str
            )
            article["images"] = [Path(p).name for p in image_paths]
            
            article_file.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"文章已保存: {article_file}")
            
            self.update_index(article)
            return [article]
        except Exception as e:
            print(f"生成失败，跳过: {e}")
            return []

    def update_index(self, article: dict):
        """更新内容索引"""
        index_file = Path("content/index.json")
        
        index = []
        if index_file.exists():
            try:
                raw = index_file.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, dict) and "articles" in data:
                    index = data["articles"]
                elif isinstance(data, list):
                    index = data
            except json.JSONDecodeError:
                print("警告: 索引文件损坏，重新创建")
                index = []
        
        index.insert(0, {
            "date": article.get("date", ""),
            "theme": article.get("theme", ""),
            "theme_name": article.get("theme_name", ""),
            "title": article.get("title", "").replace('"', "'"),
            "summary": article.get("summary", "").replace('"', "'"),
            "keywords": article.get("keywords", []),
            "images": article.get("images", [])[:1]
        })
        
        seen = set()
        unique = []
        for item in index:
            key = f"{item.get('date', '')}_{item.get('title', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        index_file.write_text(
            json.dumps({"articles": unique}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"索引已更新，共 {len(unique)} 篇文章")

    def generate_batch(self, days: int = 7):
        """批量生成未来几天的内容（用于测试）"""
        from datetime import timedelta
        
        for i in range(days):
            future = datetime.now() + timedelta(days=i)
            date_str = future.strftime("%Y-%m-%d")
            
            article_file = self.content_dir / f"{date_str}.json"
            if article_file.exists():
                continue
            
            theme = self.get_today_theme(future)
            print(f"生成 {date_str} - {theme['name']}")
            
            try:
                article = self.writer.generate_article(theme["id"], theme["name"], date_str)
                image_paths = self.finder.search_images(
                    article.get("image_prompts", []),
                    count=3,
                    date_str=date_str
                )
                article["images"] = [Path(p).name for p in image_paths]
                
                article_file.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                self.update_index(article)
            except Exception as e:
                print(f"生成失败: {e}")
                continue

    def generate_historical(self, articles_per_theme: int = 2, start_date_str: str = ""):
        """为每个主题生成历史文章，日期从指定日期倒推"""
        from datetime import timedelta
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.now() - timedelta(days=1)
        
        current_date = start_date
        article_count = 0
        
        for theme in self.config["themes"]:
            theme_id = theme["id"]
            theme_name = theme["name"]
            
            for i in range(articles_per_theme):
                date_str = current_date.strftime("%Y-%m-%d")
                
                article_file = self.content_dir / f"{date_str}.json"
                if article_file.exists():
                    print(f"跳过已存在: {date_str}")
                    current_date = current_date - timedelta(days=1)
                    continue
                
                print(f"生成 {date_str} - {theme_name}")
                
                try:
                    article = self.writer.generate_article(theme_id, theme_name, date_str)
                    image_paths = self.finder.search_images(
                        article.get("image_prompts", []),
                        count=3,
                        date_str=date_str
                    )
                    article["images"] = [Path(p).name for p in image_paths]
                    
                    article_file.write_text(
                        json.dumps(article, ensure_ascii=False, indent=2),
                        encoding="utf-8"
                    )
                    self.update_index(article)
                    article_count += 1
                except Exception as e:
                    print(f"生成失败 {date_str}: {e}")
                
                current_date = current_date - timedelta(days=1)
        
        print(f"历史文章生成完成，共 {article_count} 篇")


def main():
    parser = argparse.ArgumentParser(description="少年科普杂志生成器")
    parser.add_argument("--theme", "-t", default="", help="指定主题")
    parser.add_argument("--batch", "-b", type=int, default=0, help="批量生成N天")
    parser.add_argument("--historical", "-H", action="store_true", help="为每个主题生成历史文章")
    parser.add_argument("--count", "-c", type=int, default=2, help="每个主题生成的文章数")
    parser.add_argument("--start-date", "-s", default="", help="开始日期（YYYY-MM-DD）")
    parser.add_argument("--force-all", "-f", action="store_true", help="强制生成今日全部主题，不受批次限制")
    args = parser.parse_args()
    
    gen = MagazineGenerator()
    
    if args.historical:
        gen.generate_historical(args.count, args.start_date)
    elif args.batch > 0:
        gen.generate_batch(args.batch)
    else:
        gen.generate_daily(args.theme, force_all=args.force_all)


if __name__ == "__main__":
    main()
