#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量为主题生成文章 - 每个主题生成指定数量"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from ai_rewrite import AIWriter
from image_search import ImageFinder


def main():
    # 确保 API Key 已设置
    if not os.environ.get("AGENS_API_KEY"):
        print("错误: 请设置 AGENS_API_KEY 环境变量")
        sys.exit(1)

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    writer = AIWriter()
    finder = ImageFinder()
    content_dir = Path("content/archives")

    # 定义每个主题需要生成的文章数
    theme_counts = {
        "role_model": 2,      # 榜样人物
        "innovation": 2,      # 科学创新
        "nature": 2,          # 自然与动物
        "china_story": 2,     # 中国故事
        "classical": 1,       # 古典文化
        "military": 1,        # 少年军事
        "physics": 1,         # 物理小实验（已有1篇，再补1篇）
    }

    # 检查已有文章的主题
    existing = {}
    for f in content_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            theme = data.get("theme", "")
            existing[theme] = existing.get(theme, 0) + 1
        except Exception:
            pass

    print(f"已有文章: {existing}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_counter = len(list(content_dir.glob(f"{date_str}*.json")))

    for theme_config in config["themes"]:
        theme_id = theme_config["id"]
        theme_name = theme_config["name"]

        target = theme_counts.get(theme_id, 1)
        current = existing.get(theme_id, 0)
        need = max(0, target - current)

        if need == 0:
            print(f"\n✓ {theme_name} 已有 {current} 篇，无需生成")
            continue

        print(f"\n{'='*60}")
        print(f"主题: {theme_name} ({theme_id}) - 已有{current}篇，需生成{need}篇")
        print(f"{'='*60}")

        for i in range(need):
            file_counter += 1
            file_date_str = f"{date_str}_{file_counter}"

            print(f"\n--- [{theme_name}] 第 {i+1}/{need} 篇 ---")

            try:
                # 生成文章
                article = writer.generate_article(theme_id, theme_name, date_str)
                article["date"] = date_str
                article["file_id"] = file_date_str

                # 生成配图
                print("正在生成配图...")
                image_paths = finder.search_images(
                    article.get("image_prompts", []),
                    count=config["content"]["image_count"],
                    date_str=file_date_str
                )
                article["images"] = [Path(p).name for p in image_paths]

                # 保存
                article_file = content_dir / f"{file_date_str}.json"
                article_file.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"✓ 文章已保存: {article_file}")

                # 更新索引
                update_index(content_dir.parent / "index.json", article)

                # 更新已有计数
                existing[theme_id] = existing.get(theme_id, 0) + 1

            except Exception as e:
                print(f"✗ 生成失败: {e}")
                continue

    print(f"\n{'='*60}")
    print("全部完成！")
    print(f"{'='*60}")


def update_index(index_file, article):
    """更新索引文件"""
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


if __name__ == "__main__":
    main()
