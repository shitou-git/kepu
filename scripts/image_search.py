#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成模块 - 使用 Agnes AI 图片生成 API 为文章生成配图
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Optional


class ImageFinder:
    def __init__(self):
        self.api_key = os.environ.get("AGENS_API_KEY", "")
        self.api_base = "https://apihub.agnes-ai.com/v1"
        self.image_dir = Path("content/images")
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def search_images(self, queries: List[str], count: int = 3, date_str: str = "") -> List[str]:
        """
        使用 Agnes AI 生成图片并下载到本地
        返回本地图片路径列表
        """
        images = []
        
        if self.api_key:
            for i, query in enumerate(queries[:count]):
                image_url = self._generate_image(query)
                if image_url:
                    local_path = self._download_image(image_url, query, date_str, i+1)
                    if local_path:
                        images.append(local_path)
                if len(images) >= count:
                    break

        # 备用：使用免费图库 API
        if len(images) < count:
            images.extend(self._get_fallback_images(count - len(images), queries, date_str))

        return images[:count]

    def _generate_image(self, prompt: str) -> Optional[str]:
        """使用 Agnes AI 图片生成 API 生成图片"""
        try:
            url = f"{self.api_base}/images/generations"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "agnes-image-2.1-flash",
                "prompt": prompt,
                "size": "2K",
                "ratio": "16:9",
                "extra_body": {
                    "response_format": "url"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0].get("url")
        except Exception as e:
            print(f"Agnes AI 图片生成失败: {e}")
        return None

    def _download_image(self, url: str, query: str, date_str: str, index: int) -> Optional[str]:
        """下载图片到本地"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"{date_str}_{index}_{query_hash}.png"
            filepath = self.image_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return str(filepath)
        except Exception as e:
            print(f"图片下载失败: {e}")
            return None

    def _get_fallback_images(self, count: int, queries: List[str], date_str: str) -> List[str]:
        """备用图片获取方案"""
        images = []
        fallback_urls = [
            "https://picsum.photos/800/450",
            "https://picsum.photos/800/450?random=2",
            "https://picsum.photos/800/450?random=3"
        ]
        
        for i in range(count):
            url = fallback_urls[i % len(fallback_urls)]
            local_path = self._download_image(url, f"fallback_{i}", date_str, i+1)
            if local_path:
                images.append(local_path)
        
        return images

    def get_local_image_path(self, filename: str) -> str:
        """获取图片在构建后的相对路径"""
        return f"images/{filename}"


if __name__ == "__main__":
    import os
    os.environ["AGENS_API_KEY"] = "sk-lr4s7E7eiQYUeC4T47xNoQciOapqAIOFPkTLgvtd8ae7y6nZ"
    finder = ImageFinder()
    queries = ["kids science experiment with cornstarch, colorful illustration for children", 
               "happy children doing physics experiment in kitchen, cartoon style"]
    paths = finder.search_images(queries, count=2, date_str="2026-07-14")
    print(paths)
