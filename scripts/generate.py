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

    def get_today_theme(self, date: datetime = None, override_theme: str = "") -> dict:
        """根据日期获取今日主题"""
        if override_theme:
            for t in self.config["themes"]:
                if t["id"] == override_theme or t["name"] == override_theme:
                    return t
            print(f"警告: 未找到主题 '{override_theme}'，使用日期匹配")
        
        date = date or datetime.now()
        weekday = date.isoweekday()  # 1=周一, 7=周日
        
        for theme in self.config["themes"]:
            if weekday in theme["weekdays"]:
                return theme
        
        # 默认返回第一个主题
        return self.config["themes"][0]

    def generate_daily(self, override_theme: str = ""):
        """生成今日科普内容"""
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        
        # 检查是否已生成
        article_file = self.content_dir / f"{date_str}.json"
        if article_file.exists():
            print(f"今日内容已存在: {article_file}")
            return
        
        # 获取今日主题
        theme = self.get_today_theme(today, override_theme)
        print(f"今日主题: {theme['name']} ({theme['id']})")
        
        # 生成文章
        print("正在生成文章...")
        article = self.writer.generate_article(theme["id"], theme["name"], date_str)
        
        # 搜索配图
        print("正在搜索配图...")
        image_paths = self.finder.search_images(
            article.get("image_prompts", []),
            count=self.config["content"]["image_count"],
            date_str=date_str
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
        
        return article

    def update_index(self, article: dict):
        """更新内容索引"""
        index_file = Path("content/index.json")
        
        index = []
        if index_file.exists():
            index = json.loads(index_file.read_text(encoding="utf-8"))
        
        # 添加新条目到开头
        index.insert(0, {
            "date": article["date"],
            "theme": article["theme"],
            "theme_name": article["theme_name"],
            "title": article["title"],
            "summary": article["summary"],
            "keywords": article["keywords"],
            "images": article.get("images", [])[:1]  # 只保存首张图
        })
        
        # 去重（按日期）
        seen = set()
        unique = []
        for item in index:
            if item["date"] not in seen:
                seen.add(item["date"])
                unique.append(item)
        
        index_file.write_text(
            json.dumps(unique, ensure_ascii=False, indent=2),
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


def main():
    parser = argparse.ArgumentParser(description="少年科普杂志生成器")
    parser.add_argument("--theme", "-t", default="", help="指定主题")
    parser.add_argument("--batch", "-b", type=int, default=0, help="批量生成N天")
    args = parser.parse_args()
    
    gen = MagazineGenerator()
    
    if args.batch > 0:
        gen.generate_batch(args.batch)
    else:
        gen.generate_daily(args.theme)


if __name__ == "__main__":
    main()
