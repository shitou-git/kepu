#!/usr/bin/env python3
"""清洗文章中的口语词汇"""

import json
import re
from pathlib import Path

# 需要清洗的口语词汇及其处理方式
CLEANUP_RULES = [
    # 直接删除的口语（通常出现在句首或独立成句）
    (r'你知道吗[，、。！？]?', ''),
    (r'试想一下[，、。]?', ''),
    (r'想象一下[，、。]?', ''),
    (r'想一想[，、。]?', ''),
    (r'你有没有想过[，、。]?', ''),
    (r'你有没有发现[，、。]?', ''),
    (r'你有没有注意到[，、。]?', ''),
    (r'你有没有[，、。]?', ''),

    # "不妨"替换为"可以"
    (r'不妨', '可以'),

    # "是不是"问句转换为更自然的表达
    (r'是不是([^？。\n]{1,30})[？]', r'\1吗？'),
    (r'是不是([^？。\n]{1,30})呢[？]?', r'\1吗？'),

    # "你会发现"转换为直接陈述
    (r'你会发现[,，]?([^。！？\n]+)[。！]', r'\1。'),

    # 清理多余的标点和空行
    (r'[，,]\s*[。！？]', '。'),
    (r'\n{3,}', '\n\n'),
]

def clean_content(text: str) -> str:
    """清洗文本中的口语词汇"""
    original = text

    for pattern, replacement in CLEANUP_RULES:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)

    # 清理句首多余的标点
    text = re.sub(r'^[，,、]+', '', text, flags=re.MULTILINE)

    # 清理连续标点
    text = re.sub(r'[。]{2,}', '。', text)
    text = re.sub(r'[！？]{2,}', '！', text)

    return text

def clean_article_file(filepath: Path) -> bool:
    """清洗单篇文章，返回是否有修改"""
    data = json.loads(filepath.read_text(encoding='utf-8'))
    modified = False

    # 清洗正文
    if 'content' in data:
        original = data['content']
        cleaned = clean_content(original)
        if cleaned != original:
            data['content'] = cleaned
            modified = True
            print(f"  - 正文已清洗")

    # 清洗知识卡片
    if 'fact_card' in data and isinstance(data['fact_card'], list):
        new_facts = []
        for fact in data['fact_card']:
            cleaned = clean_content(fact)
            new_facts.append(cleaned)
            if cleaned != fact:
                modified = True
        data['fact_card'] = new_facts

    # 清洗思考题
    if 'thinking' in data and isinstance(data['thinking'], list):
        new_thinking = []
        for q in data['thinking']:
            cleaned = clean_content(q)
            new_thinking.append(cleaned)
            if cleaned != q:
                modified = True
        data['thinking'] = new_thinking

    if modified:
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    return modified

def main():
    content_dir = Path('/workspace/content/archives')
    files = sorted(content_dir.glob('*.json'))

    print(f"找到 {len(files)} 篇文章")

    cleaned_count = 0
    for filepath in files:
        print(f"\n处理: {filepath.name}")
        if clean_article_file(filepath):
            cleaned_count += 1

    print(f"\n\n===== 完成 =====")
    print(f"已清洗: {cleaned_count}/{len(files)} 篇")

if __name__ == '__main__':
    main()