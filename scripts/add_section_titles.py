#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为已有文章批量添加小节标题
不需要重新生成整篇文章，只根据现有内容生成小标题插入
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
    """从文章内容中提取所有小节的正文"""
    parts = re.split(r'\[IMAGE_\d+\]', content)
    if len(parts) < 2:
        return []
    
    first_part = parts[0].strip()
    paragraphs = first_part.split('\n\n')
    
    sections = []
    if len(paragraphs) <= 1:
        sections.append(first_part)
    else:
        sections.append('\n\n'.join(paragraphs[1:]))
    
    for i in range(1, len(parts)):
        section = parts[i].strip()
        if section:
            sections.append(section)
    
    return sections


def insert_titles(content: str, titles: list) -> str:
    """将小节标题插入到文章内容中"""
    if len(titles) < 1:
        return content
    
    parts = re.split(r'(\[IMAGE_\d+\])', content)
    if len(parts) < 2:
        return content
    
    first_part = parts[0].strip()
    paragraphs = first_part.split('\n\n')
    
    if len(paragraphs) <= 1:
        new_content = first_part + f"\n\n### {titles[0]}\n\n"
    else:
        summary = paragraphs[0]
        rest = '\n\n'.join(paragraphs[1:])
        new_content = summary + f"\n\n### {titles[0]}\n\n" + rest
    
    title_idx = 1
    i = 1
    while i < len(parts):
        image_tag = parts[i]
        new_content += "\n\n" + image_tag
        
        if i + 1 < len(parts):
            section = parts[i + 1].strip()
            if section and title_idx < len(titles):
                new_content += f"\n\n### {titles[title_idx]}\n\n" + section
                title_idx += 1
            elif section:
                new_content += "\n\n" + section
        i += 2
    
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
        print(f"  Read failed: {e}")
        return False
    
    content = data.get('content', '')
    theme_name = data.get('theme_name', '')
    
    if has_section_titles(content):
        print(f"  Already has section titles, skip")
        return False
    
    sections = extract_sections(content)
    if len(sections) < 2 or not all(s.strip() for s in sections):
        print(f"  Sections incomplete ({len(sections)} sections), skip")
        return False
    
    print(f"  Theme: {theme_name}")
    print(f"  Sections: {len(sections)}")
    print(f"  Generating section titles...")
    
    try:
        titles = writer.generate_section_titles(sections, theme_name)
    except Exception as e:
        print(f"  Generate titles failed: {e}")
        return False
    
    if len(titles) < len(sections):
        print(f"  Not enough titles ({len(titles)}/{len(sections)}), skip")
        return False
    
    titles = titles[:len(sections)]
    print(f"  Titles: {titles}")
    
    new_content = insert_titles(content, titles)
    
    if dry_run:
        print(f"  [Dry run] No actual changes")
        return True
    
    data['content'] = new_content
    data['section_count'] = len(sections)
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"  Updated: {file_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Add section titles to existing articles")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Dry run mode, no actual changes")
    parser.add_argument("--file", "-f", default="", help="Only process specified file")
    args = parser.parse_args()
    
    writer = AIWriter()
    content_dir = Path("content/archives")
    
    if not content_dir.exists():
        print("Content directory not found")
        return
    
    if args.file:
        files = [content_dir / args.file]
        if not files[0].exists():
            print(f"File not found: {files[0]}")
            return
    else:
        files = sorted(content_dir.glob("*.json"))
    
    print(f"Found {len(files)} articles")
    print()
    
    success_count = 0
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {file_path.name}")
        if process_article(file_path, writer, args.dry_run):
            success_count += 1
        print()
    
    print(f"Done, successfully added titles: {success_count}/{len(files)}")


if __name__ == "__main__":
    main()
