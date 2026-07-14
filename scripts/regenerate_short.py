#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成内容过短的文章（按新的1500字标准）
保持原 file_id、日期、主题不变，只重写正文内容和配图
"""

import os
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_rewrite import AIWriter
from image_search import ImageFinder


# 字数低于此阈值的文章将被重新生成
MIN_CHAR_COUNT = 1000


def count_chars(content: str) -> int:
    """统计正文字数（去除图片标记和markdown符号）"""
    text = re.sub(r'\[IMAGE_\d+\]', '', content)
    text = re.sub(r'[#*>\-]', '', text)
    return len(text.replace(' ', '').replace('\n', ''))


def main():
    # 设置 API Key
    api_key = "sk-lr4s7E7eiQYUeC4T47xNoQciOapqAIOFPkTLgvtd8ae7y6nZ"
    os.environ["AGENS_API_KEY"] = api_key

    archives_dir = Path("content/archives")
    writer = AIWriter()

    # 找出所有过短的文章
    short_articles = []
    for f in sorted(archives_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        char_count = count_chars(data.get("content", ""))
        if char_count < MIN_CHAR_COUNT:
            short_articles.append((f, data, char_count))

    print(f"找到 {len(short_articles)} 篇字数少于 {MIN_CHAR_COUNT} 的文章需要重新生成")
    print(f"策略: 只重新生成文本内容，保留原有图片引用\n")

    success_count = 0
    fail_count = 0

    for idx, (file_path, old_data, old_count) in enumerate(short_articles, 1):
        file_id = file_path.stem
        theme_id = old_data.get("theme", "")
        theme_name = old_data.get("theme_name", "")
        date_str = old_data.get("date", file_id)

        print(f"[{idx}/{len(short_articles)}] 重新生成: {file_id} ({old_count}字)")
        print(f"  主题: {theme_name} | 标题: {old_data.get('title', '')[:30]}")

        try:
            # 只生成新文章文本（不生成图片，保留原图）
            new_article = writer.generate_article(theme_id, theme_name, date_str)
            # 保留原 file_id 和 date
            new_article["file_id"] = file_id
            new_article["date"] = date_str
            # 保留原有图片引用和图片提示词（原图片与新内容可能略有出入，但避免重新生成图片耗时过长）
            new_article["images"] = old_data.get("images", [])

            # 保存
            file_path.write_text(
                json.dumps(new_article, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            new_count = count_chars(new_article.get("content", ""))
            print(f"  完成: {old_count}字 -> {new_count}字\n")
            success_count += 1

        except Exception as e:
            print(f"  失败: {e}\n")
            fail_count += 1
            continue

    print(f"\n重新生成完成：成功 {success_count} 篇，失败 {fail_count} 篇")


if __name__ == "__main__":
    main()
