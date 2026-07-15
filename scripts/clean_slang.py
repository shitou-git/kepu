#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清洗文章中的口头禅：说白了、说实话、你想想、这么说吧"""

import json
import re
from pathlib import Path


# 需要清除的口头禅及其清洗规则
# 每条规则：(正则模式, 替换函数说明)
SLANG_PATTERNS = [
    # "说白了，" / "说白了" / "说白了就是"
    (r'[，,]?\s*说白了[，,]?\s*', ''),
    (r'说白了[，,]?\s*', ''),
    # "说实话，" / "说实话"
    (r'[，,]?\s*说实话[，,]?\s*', ''),
    (r'说实话[，,]?\s*', ''),
    # "你想想，" / "你想想看，" / "你想想"
    (r'[，,]?\s*你想想看[，,]?\s*', ''),
    (r'[，,]?\s*你想想[，,]?\s*', ''),
    # "这么说吧，" / "这么说吧"
    (r'[，,]?\s*这么说吧[，,]?\s*', ''),
    (r'这么说吧[，,]?\s*', ''),
]


def clean_text(text):
    """清洗文本中的口头禅"""
    if not text:
        return text

    original = text
    for pattern, replacement in SLANG_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # 清理可能产生的多余标点和空格
    # 合并连续逗号
    text = re.sub(r'，[，,]+', '，', text)
    text = re.sub(r'[，,]{2,}', '，', text)
    # 清理句首逗号（只清行首的逗号，不碰换行）
    text = re.sub(r'(?<=\n)[，,]+', '', text)
    text = re.sub(r'^[，,]+', '', text)
    # 清理换行后的逗号（注意：\s 不能包含 \n，否则会吞掉段落分隔的空行）
    text = re.sub(r'\n[，, \t]+', '\n', text)
    # 合并多余空行，保留段落分隔
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def main():
    archives_dir = Path("content/archives")
    total_cleaned = 0

    for f in sorted(archives_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))

        content = data.get("content", "")
        if not content:
            continue

        # 统计清洗前
        keywords = ["说白了", "说实话", "你想想", "这么说吧"]
        before_count = sum(content.count(k) for k in keywords)

        if before_count == 0:
            continue

        # 清洗正文
        cleaned_content = clean_text(content)

        # 统计清洗后
        after_count = sum(cleaned_content.count(k) for k in keywords)

        if cleaned_content != content:
            data["content"] = cleaned_content
            f.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            removed = before_count - after_count
            total_cleaned += removed
            print(f"✓ {f.name}: 删除{removed}处口头禅 ({before_count}→{after_count})")

    print(f"\n清洗完成！共删除 {total_cleaned} 处口头禅")


if __name__ == "__main__":
    main()
