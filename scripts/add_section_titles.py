#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为已有文章批量添加小节标题
不需要重新生成整篇文章，只根据现有内容生成3个小标题插入
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_rewrite import AIWriter


def extract_sections(content: str) -> list:
    """从文章内容中提取3个小节的正文"""
    parts = re.split(r'\[IMAGE_\d+\]', content)
    if len(parts) < 3:
        return []
    
    first_part = parts[0].strip()
    paragraphs = first_part.split('\n\n')
    
    if len(paragraphs) <= 1:
        section1 = first_part
    else:
        section1 = '\n\n'.join(paragraphs[1:])
    
    section2 = parts[1].strip()
    section3 = parts[2].strip() if len(parts) > 2 else ""
    
    return [section1, section2, section3]


def insert_titles(content: str, titles: list) -> str:
    """将3个小节标题插入到文章内容中"""
    if len(titles) < 3:
        return content
    
    parts = re.split(r'(\[IMAGE_\d+\])', content)
    if len(parts) < 5:
        return content
    
    first_part = parts[0].strip()
    paragraphs = first_part.split('\n\n')
    
    if len(paragraphs) <= 1:
        new_first = first_part + f"\n\n### {titles[0]}\n\n"
    else:
        summary = paragraphs[0]
        rest = '\n\n'.join(paragraphs[1:])
        new_first = summary + f"\n\n### {titles[0]}\n\n" + rest
    
    image1 = parts[1]
    section2 = parts[2].strip()
    image2 = parts[3]
    section3 = parts[4].strip()
    rest = ''.join(parts[5:]) if len(parts) > 5 else ""
    
    new_content = (
        new_first + "\n\n" +
        image1 + "\n\n" +
        f"### {titles[1]}\n\n" + section2 + "\n\n" +
        image2 + "\n\n" +
        f"### {titles[2]}\n\n" + section3 +
        rest
    )
    
    new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip()
    
    return new_content


def has_section_titles(content: str) -> bool:
    """检查文章是否已经有小节标题"""
    return bool(re.search(r'^###\s+', content, re.MULTILINE))


def process_article(file_path: Path, writer: AIWriter, dry_run: bool = False) -> bool:
    """处理单篇文章"""
    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"  读取失败: {e}")
        return False
    
    content = data.get('content', '')
    theme_name = data.get('theme_name', '')
    
    if has_section_titles(content):
        print(f"  已有小节标题，跳过")
        return False
    
    sections = extract_sections(content)
    if len(sections) < 3 or not all(sections):
        print(f"  分段不完整，跳过")
        return False
    
    print(f"  主题: {theme_name}")
    print(f"  正在生成小节标题...")
    
    try:
        titles = writer.generate_section_titles(sections, theme_name)
    except Exception as e:
        print(f"  生成标题失败: {e}")
        return False
    
    if len(titles) < 3:
        print(f"  标题数量不足（{len(titles)}/3），跳过")
        return False
    
    print(f"  标题: {titles}")
    
    new_content = insert_titles(content, titles)
    
    if dry_run:
        print(f"  [预览模式] 不会实际修改文件")
        return True
    
    data['content'] = new_content
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"  已更新: {file_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="为已有文章批量添加小节标题")
    parser.add_argument("--dry-run", "-d", action="store_true", help="预览模式，不实际修改文件")
    parser.add_argument("--file", "-f", default="", help="只处理指定文件")
    args = parser.parse_args()
    
    writer = AIWriter()
    content_dir = Path("content/archives")
    
    if not content_dir.exists():
        print("内容目录不存在")
        return
    
    if args.file:
        files = [content_dir / args.file]
        if not files[0].exists():
            print(f"文件不存在: {files[0]}")
            return
    else:
        files = sorted(content_dir.glob("*.json"))
    
    print(f"共找到 {len(files)} 篇文章")
    print()
    
    success_count = 0
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 处理: {file_path.name}")
        if process_article(file_path, writer, args.dry_run):
            success_count += 1
        print()
    
    print(f"处理完成，成功添加标题: {success_count}/{len(files)} 篇")


if __name__ == "__main__":
    main()
