#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用新的去AI化风格改写所有现有文章
- 保持原标题不变
- 重新生成内容、图片提示词
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


def main():
    writer = AIWriter()
    finder = ImageFinder()
    content_dir = Path("content/archives")

    # 获取所有文章文件
    article_files = sorted(content_dir.glob("*.json"))
    print(f"共 {len(article_files)} 篇文章需要改写\n")

    success_count = 0
    fail_count = 0

    for idx, article_file in enumerate(article_files):
        print(f"\n{'='*60}")
        print(f"[{idx+1}/{len(article_files)}] 处理: {article_file.name}")
        print(f"{'='*60}")

        try:
            # 读取原文章
            original = json.loads(article_file.read_text(encoding="utf-8"))
            title = original.get("title", "")
            theme = original.get("theme", "")
            theme_name = original.get("theme_name", "")
            date_str = original.get("date", "")
            summary = original.get("summary", "")
            file_id = original.get("file_id", date_str)

            if not title or not theme:
                print(f"  跳过: 缺少标题或主题信息")
                fail_count += 1
                continue

            print(f"  标题: {title}")
            print(f"  主题: {theme_name} ({theme})")
            print(f"  日期: {date_str}")

            # 用新风格改写文章
            print("  正在改写文章...")
            article = writer.rewrite_existing_article(
                theme=theme,
                theme_name=theme_name,
                date_str=date_str,
                title=title,
                summary=summary
            )

            # 保持原有元数据
            article["date"] = date_str
            article["file_id"] = file_id

            # 生成新配图
            print("  正在生成配图...")
            image_paths = finder.search_images(
                article.get("image_prompts", []),
                count=3,
                date_str=file_id
            )
            article["images"] = [Path(p).name for p in image_paths]

            # 保存
            article_file.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"  已保存: {article_file}")
            print(f"  图片: {article['images']}")
            success_count += 1

            # 间隔一下，避免API限流
            time.sleep(2)

        except Exception as e:
            print(f"  改写失败: {e}")
            fail_count += 1
            continue

    print(f"\n{'='*60}")
    print(f"全部完成！成功 {success_count} 篇，失败 {fail_count} 篇")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
