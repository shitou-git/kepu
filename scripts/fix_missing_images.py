#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补充缺失的图片"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from image_search import ImageFinder


def main():
    if not os.environ.get("AGENS_API_KEY"):
        print("错误: 请设置 AGENS_API_KEY 环境变量")
        sys.exit(1)
    
    finder = ImageFinder()
    
    articles = [
        ("content/archives/2026-07-13.json", 3),
        ("content/archives/2026-07-14.json", 3),
    ]
    
    for article_path_str, target_count in articles:
        article_path = Path(article_path_str)
        if not article_path.exists():
            print(f"跳过: {article_path} 不存在")
            continue
        
        data = json.loads(article_path.read_text(encoding="utf-8"))
        file_id = data.get("file_id", article_path.stem)
        prompts = data.get("image_prompts", [])
        current_images = data.get("images", [])
        
        print(f"\n处理: {data['title'][:30]}")
        print(f"当前图片: {len(current_images)}/{len(prompts)}")
        
        for i in range(len(prompts)):
            if i >= len(current_images) or not current_images[i]:
                print(f"  生成第{i+1}张图片...")
                image_url = finder._generate_image(prompts[i])
                if image_url:
                    local_path = finder._download_image(image_url, prompts[i], file_id, i + 1)
                    if local_path:
                        while len(current_images) <= i:
                            current_images.append("")
                        current_images[i] = Path(local_path).name
                        print(f"    ✓ 成功")
                    else:
                        print(f"    ✗ 下载失败")
                else:
                    print(f"    ✗ 生成失败")
        
        if len(current_images) > len(data.get("images", [])):
            data["images"] = current_images
            article_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"  更新文章: {len(current_images)}张图片")
    
    print("\n所有图片补充完成！")


if __name__ == "__main__":
    main()
