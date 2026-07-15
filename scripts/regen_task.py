#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新生成指定文章和图片"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_rewrite import AIWriter
from image_search import ImageFinder


def regen_image_prompt(original_prompt):
    """优化图片提示词，确保没有畸形人物"""
    improvements = [
        ", ensure the character has exactly two arms and two legs, no extra limbs",
        ", character anatomy is correct with natural human proportions",
        ", avoid any distorted or duplicated body parts"
    ]
    return original_prompt + "".join(improvements)


def regen_single_image(article_file, image_index):
    """重新生成单张图片"""
    data = json.loads(article_file.read_text(encoding="utf-8"))
    prompts = data.get("image_prompts", [])
    
    if image_index >= len(prompts):
        print(f"错误：文章只有 {len(prompts)} 个图片提示词")
        return False
    
    file_id = data.get("file_id", "")
    if not file_id:
        file_id = article_file.stem
    
    finder = ImageFinder()
    
    improved_prompt = regen_image_prompt(prompts[image_index])
    print(f"重新生成第{image_index+1}张图片，提示词已优化...")
    
    image_url = finder._generate_image(improved_prompt)
    if image_url:
        local_path = finder._download_image(image_url, improved_prompt, file_id, image_index + 1)
        if local_path:
            # 更新文章的图片列表
            images = data.get("images", [])
            while len(images) <= image_index:
                images.append("")
            images[image_index] = Path(local_path).name
            data["images"] = images
            
            article_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"✓ 第{image_index+1}张图片已更新")
            return True
        else:
            print(f"✗ 图片下载失败")
    else:
        print(f"✗ 图片生成失败")
    
    return False


def regen_article(theme_id, theme_name, date_str, file_id):
    """重新生成整篇文章"""
    content_dir = Path("content/archives")
    article_file = content_dir / f"{file_id}.json"
    
    print(f"\n{'='*60}")
    print(f"重新生成: {theme_name} - {date_str}")
    print(f"{'='*60}")
    
    # 删除旧文章和图片
    if article_file.exists():
        data = json.loads(article_file.read_text(encoding="utf-8"))
        old_images = data.get("images", [])
        for img in old_images:
            img_path = Path("content/images") / img
            if img_path.exists():
                img_path.unlink()
                print(f"删除旧图片: {img}")
        article_file.unlink()
        print("删除旧文章")
    
    writer = AIWriter()
    finder = ImageFinder()
    
    article = writer.generate_article(theme_id, theme_name, date_str)
    article["date"] = date_str
    article["file_id"] = file_id
    
    print("正在生成配图...")
    image_paths = finder.search_images(
        article.get("image_prompts", []),
        count=3,
        date_str=file_id
    )
    article["images"] = [Path(p).name for p in image_paths]
    
    article_file.write_text(
        json.dumps(article, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✓ 文章已保存: {article_file}")
    
    update_index(article)
    return True


def update_index(article):
    """更新索引"""
    index_file = Path("content/index.json")
    index = []
    if index_file.exists():
        try:
            raw = index_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict) and "articles" in data:
                index = data["articles"]
            elif isinstance(data, list):
                index = data
        except json.JSONDecodeError:
            index = []
    
    new_entry = {
        "date": article.get("date", ""),
        "theme": article.get("theme", ""),
        "theme_name": article.get("theme_name", ""),
        "title": article.get("title", "").replace('"', "'"),
        "summary": article.get("summary", "").replace('"', "'"),
        "keywords": article.get("keywords", []),
        "images": article.get("images", [])[:1]
    }
    
    index = [new_entry] + [i for i in index if i.get("title") != new_entry["title"]]
    
    seen = set()
    unique = []
    for item in index:
        key = f"{item.get('date', '')}_{item.get('title', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(item)
    
    index_file.write_text(
        json.dumps({"articles": unique}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main():
    if not os.environ.get("AGENS_API_KEY"):
        print("错误: 请设置 AGENS_API_KEY 环境变量")
        sys.exit(1)
    
    # 任务1: 重新生成少年军事第3张图片
    military_file = Path("content/archives/2026-07-15_10.json")
    if military_file.exists():
        print("任务1: 重新生成少年军事第3张图片...")
        regen_single_image(military_file, 2)
    
    # 任务2: 重新生成航空航天文章
    print("\n任务2: 重新生成两篇航空航天文章...")
    
    # 从纸飞机到空间站：航空航天带你摸星星的秘密
    regen_article("aerospace", "航空航天", "2026-07-13", "2026-07-13")
    
    # 带着风筝去太空：航空航天大冒险
    regen_article("aerospace", "航空航天", "2026-07-14", "2026-07-14")
    
    print("\n所有任务完成！")


if __name__ == "__main__":
    main()
