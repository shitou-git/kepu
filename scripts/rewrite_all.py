#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用新的去AI化风格改写所有现有文章
- 保持原标题不变
- 解析失败时保留原文
- 重新生成配图
"""

import os
import sys
import json
import time
from pathlib import Path

os.environ["AGENS_API_KEY"] = "sk-lr4s7E7eiQYUeC4T47xNoQciOapqAIOFPkTLgvtd8ae7y6nZ"

sys.path.insert(0, str(Path(__file__).parent))
from ai_rewrite import AIWriter
from image_search import ImageFinder


def is_article_valid(article: dict) -> bool:
    """检查文章是否完整"""
    if not article.get("title"):
        return False
    if not article.get("content") or len(article["content"]) < 500:
        return False
    if not article.get("fact_card") or len(article["fact_card"]) < 2:
        return False
    if not article.get("thinking") or len(article["thinking"]) < 1:
        return False
    if not article.get("image_prompts") or len(article["image_prompts"]) < 2:
        return False
    return True


def main():
    writer = AIWriter()
    finder = ImageFinder()
    content_dir = Path("content/archives")

    article_files = sorted(content_dir.glob("*.json"))
    print(f"共 {len(article_files)} 篇文章需要检查\n")

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for idx, article_file in enumerate(article_files):
        print(f"\n{'='*60}")
        print(f"[{idx+1}/{len(article_files)}] 处理: {article_file.name}")
        print(f"{'='*60}")

        try:
            original = json.loads(article_file.read_text(encoding="utf-8"))
            title = original.get("title", "")
            theme = original.get("theme", "")
            theme_name = original.get("theme_name", "")
            date_str = original.get("date", "")
            file_id = original.get("file_id", date_str)

            if not title or not theme:
                print(f"  跳过: 缺少标题或主题信息")
                skipped_count += 1
                continue

            print(f"  标题: {title}")
            print(f"  主题: {theme_name} ({theme})")

            if is_article_valid(original):
                print(f"  文章已完整，跳过改写")
                skipped_count += 1
                continue

            print(f"  文章不完整，需要改写...")

            article = writer.rewrite_existing_article(
                theme=theme,
                theme_name=theme_name,
                date_str=date_str,
                title=title,
                summary=original.get("summary", "")
            )

            if not is_article_valid(article):
                print(f"  改写后仍不完整，保留原文")
                failed_count += 1
                continue

            article["date"] = date_str
            article["file_id"] = file_id

            print("  正在生成配图...")
            try:
                image_paths = finder.search_images(
                    article.get("image_prompts", []),
                    count=3,
                    date_str=file_id
                )
                article["images"] = [Path(p).name for p in image_paths]
            except Exception as img_err:
                print(f"  配图生成失败: {img_err}，使用原有图片")
                article["images"] = original.get("images", [])

            article_file.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"  已保存: {article_file}")
            success_count += 1

            time.sleep(3)

        except Exception as e:
            print(f"  处理失败: {e}")
            failed_count += 1
            continue

    print(f"\n{'='*60}")
    print(f"全部完成！")
    print(f"  成功改写: {success_count}")
    print(f"  保留原文: {failed_count}")
    print(f"  跳过(已完整): {skipped_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
