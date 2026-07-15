#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新生成指定文章的所有图片"""

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
        "content/archives/2026-07-13.json",
        "content/archives/2026-07-14.json",
    ]
    
    for article_path_str in articles:
        article_path = Path(article_path_str)
        if not article_path.exists():
            print(f"跳过: {article_path} 不存在")
            continue
        
        data = json.loads(article_path.read_text(encoding="utf-8"))
        file_id = data.get("file_id", article_path.stem)
        prompts = data.get("image_prompts", [])
        
        print(f"\n{'='*60}")
        print(f"重新生成图片: {data['title'][:30]}")
        print(f"{'='*60}")
        
        new_images = []
        for i, prompt in enumerate(prompts):
            success = False
            retries = 3
            for attempt in range(retries):
                print(f"\n  第{i+1}张图片 (尝试 {attempt+1}/{retries})...")
                image_url = finder._generate_image(prompt)
                if image_url:
                    local_path = finder._download_image(image_url, prompt, file_id, i + 1)
                    if local_path:
                        new_images.append(Path(local_path).name)
                        print(f"    ✓ 成功")
                        success = True
                        break
                    else:
                        print(f"    ✗ 下载失败")
                else:
                    print(f"    ✗ 生成失败")
            
            if not success:
                print(f"    ⚠️ 跳过（宁缺毋滥）")
        
        if new_images:
            data["images"] = new_images
            article_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"\n  更新文章: {len(new_images)}/{len(prompts)} 张图片")
    
    print("\n所有图片重新生成完成！")


if __name__ == "__main__":
    main()
