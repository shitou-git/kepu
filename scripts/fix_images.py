#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复现有文章的图片问题：
1. 清理图片提示词中的 [IMAGE_N] 前缀
2. 规范化正文图片标记（修正编号、格式、位置）
3. 图片标记不足3个时，在合适位置补充
"""

import json
import re
from pathlib import Path


def normalize_image_prompts(prompts: list) -> list:
    """清理图片提示词的前缀"""
    cleaned = []
    for p in prompts:
        p = re.sub(r'^\[IMAGE_\d+\]\s*', '', p)
        p = re.sub(r'^IMAGE_\d+[:：]\s*', '', p)
        p = re.sub(r'^\d+[\.\)、]\s*', '', p)
        p = p.strip()
        if p:
            cleaned.append(p)
    return cleaned[:3]


def normalize_content(content: str) -> str:
    """规范化正文中的图片标记：修正编号、格式、位置"""
    lines = content.split('\n')
    new_lines = []
    image_markers_found = []

    for line in lines:
        stripped = line.strip()

        # 整行都是图片标记
        if re.match(r'^[\*\s]*\[IMAGE_\d+\][\*\s]*$', stripped) or re.match(r'^!\[IMAGE_\d+\]$', stripped):
            m = re.search(r'IMAGE_(\d+)', stripped)
            if m:
                img_num = int(m.group(1))
                new_lines.append(f'[IMAGE_{img_num}]')
                image_markers_found.append(img_num)
                continue

        # 图片标记嵌在段落中
        if '[IMAGE_' in stripped:
            markers_in_line = re.findall(r'[!*]*\[IMAGE_(\d+)\][*]*', stripped)
            clean_line = re.sub(r'[!*]*\[IMAGE_\d+\][*]*', '', stripped).strip()

            if clean_line:
                new_lines.append(clean_line)

            for m_str in markers_in_line:
                img_num = int(re.search(r'(\d+)', m_str).group())
                new_lines.append(f'[IMAGE_{img_num}]')
                image_markers_found.append(img_num)
            continue

        new_lines.append(line)

    # 重新编号
    if image_markers_found:
        seen = set()
        unique_order = []
        for n in image_markers_found:
            if n not in seen:
                seen.add(n)
                unique_order.append(n)

        num_map = {old: new for new, old in enumerate(unique_order, 1)}

        final_lines = []
        for line in new_lines:
            stripped = line.strip()
            m = re.match(r'^\[IMAGE_(\d+)\]$', stripped)
            if m:
                old_num = int(m.group(1))
                new_num = num_map.get(old_num, old_num)
                if new_num <= 3:
                    final_lines.append(f'[IMAGE_{new_num}]')
            else:
                final_lines.append(line)

        content = '\n'.join(final_lines)

    # 确保图片标记前后有空行
    content = re.sub(r'(\S)\n\[IMAGE_', r'\1\n\n[IMAGE_', content)
    content = re.sub(r'\[IMAGE_(\d+)\]\n(\S)', r'[IMAGE_\1]\n\n\2', content)

    return content


def supplement_image_markers(content: str, target_count: int = 3) -> str:
    """如果图片标记不足3个，在合适位置补充"""
    existing = re.findall(r'\[IMAGE_(\d+)\]', content)
    existing_nums = sorted(set(int(x) for x in existing))

    if len(existing_nums) >= target_count:
        return content

    # 找出段落（按空行分割）
    paragraphs = re.split(r'\n\s*\n', content.strip())

    # 过滤掉标题行、图片标记行等，找出真正的正文段落
    text_paragraphs = []
    for i, para in enumerate(paragraphs):
        stripped = para.strip()
        if not stripped:
            continue
        # 跳过纯图片标记
        if re.match(r'^\[IMAGE_\d+\]$', stripped):
            continue
        # 跳过标题行
        if stripped.startswith('#'):
            continue
        # 跳过太短的（<50字）
        if len(stripped) < 50:
            continue
        text_paragraphs.append((i, para))

    needed = target_count - len(existing_nums)

    if not text_paragraphs or needed <= 0:
        return content

    # 在段落之间均匀插入图片标记
    num_to_insert = min(needed, len(text_paragraphs))
    # 从后往前插入，避免索引偏移
    insert_positions = []
    step = max(1, len(text_paragraphs) // (num_to_insert + 1))
    for k in range(num_to_insert):
        idx = min(k * step + step, len(text_paragraphs) - 1)
        para_idx = text_paragraphs[idx][0]
        insert_positions.append(para_idx)

    # 按从后往前的顺序插入
    next_num = max(existing_nums) + 1 if existing_nums else 1
    for pos in sorted(insert_positions, reverse=True):
        marker = f'[IMAGE_{next_num}]'
        paragraphs.insert(pos + 1, marker)
        next_num += 1

    return '\n\n'.join(paragraphs)


def main():
    archives_dir = Path("content/archives")
    fixed_count = 0

    for f in sorted(archives_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        original_content = data.get("content", "")
        original_prompts = data.get("image_prompts", [])

        # 1. 清理图片提示词
        new_prompts = normalize_image_prompts(original_prompts)

        # 2. 规范化图片标记
        normalized = normalize_content(original_content)

        # 3. 补充图片标记到3个
        final_content = supplement_image_markers(normalized, 3)

        # 4. 再次规范化（补充后重新编号）
        final_content = normalize_content(final_content)

        # 检查是否有变化
        prompts_changed = new_prompts != original_prompts
        content_changed = final_content != original_content

        if prompts_changed or content_changed:
            data["image_prompts"] = new_prompts
            data["content"] = final_content
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            markers = re.findall(r'\[IMAGE_\d+\]', final_content)
            unique_markers = sorted(set(markers))
            print(f"{f.stem}: 已修复")
            if prompts_changed:
                print(f"  提示词: {len(original_prompts)} -> {len(new_prompts)} (已清理前缀)")
            if content_changed:
                print(f"  图片标记: {unique_markers}")
            fixed_count += 1

    print(f"\n共修复 {fixed_count} 篇文章")


if __name__ == "__main__":
    main()
