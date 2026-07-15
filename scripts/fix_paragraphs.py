#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 clean_slang.py 误伤的段落分隔：把被压成单换行的段落恢复为双换行"""

import json
import re
from pathlib import Path


def fix_paragraphs(text: str) -> str:
    """把单换行恢复为双换行（段落分隔）"""
    if not text:
        return text

    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 先把 3 个以上换行压缩为 2 个
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 把单个换行（前后都不是换行）替换为双换行
    # 这样原本的 \n\n 不受影响，单 \n 变成 \n\n
    text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)

    # 再次压缩，防止相邻合并产生多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 去掉首尾空白
    return text.strip()


def main():
    archives_dir = Path("content/archives")
    fixed = 0

    for f in sorted(archives_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        content = data.get("content", "")
        if not content:
            continue

        new_content = fix_paragraphs(content)
        if new_content != content:
            data["content"] = new_content
            f.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            fixed += 1
            print(f"✓ {f.name}: 段落分隔已恢复")

    print(f"\n修复完成，共处理 {fixed} 篇文章")


if __name__ == "__main__":
    main()
