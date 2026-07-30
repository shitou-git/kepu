#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回填脚本 - 为现有文章生成 AI 组词字典 word_dict
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ai_rewrite import AIWriter


def main():
    writer = AIWriter()
    archives_dir = Path("content/archives")
    files = sorted(archives_dir.glob("*.json"))

    total = len(files)
    done = 0
    skipped = 0
    failed = 0

    print(f"共 {total} 篇文章需要检查")

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [跳过] 读取失败 {f.name}: {e}")
            failed += 1
            continue

        if data.get("word_dict"):
            print(f"  [跳过] {f.name} 已有 word_dict ({len(data['word_dict'])} 字)")
            skipped += 1
            continue

        content = data.get("content", "")
        if not content:
            print(f"  [跳过] {f.name} 无内容")
            skipped += 1
            continue

        print(f"  [处理] {f.name} ({data.get('title', '无标题')})...")
        try:
            word_dict = writer.generate_word_dict(content)
            data["word_dict"] = word_dict
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"    完成: {len(word_dict)} 个字")
            done += 1
            time.sleep(2)  # 避免 API 限流
        except Exception as e:
            print(f"    [失败] {e}")
            failed += 1

    print(f"\n总结: 处理 {done} 篇, 跳过 {skipped} 篇, 失败 {failed} 篇")


if __name__ == "__main__":
    main()
