#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片搜索模块 - 为文章搜索合适的配图
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Optional


class ImageFinder:
    def __init__(self):
        self.unsplash_key = os.environ.get("UNSPLASH_API_KEY", "")
        self.image_dir = Path("content/images")
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def search_images(self, queries: List[str], count: int = 3, date_str: str = "") -> List[str]:
        """
        搜索图片并下载到本地
        返回本地图片路径列表
        """
        images = []
        
        # 优先使用 Unsplash API
        if self.unsplash_key:
            for query in queries[:count]:
                url = self._search_unsplash(query)
                if url:
                    local_path = self._download_image(url, query, date_str)
                    if local_path:
                        images.append(local_path)
                if len(images) >= count:
                    break

        # 备用：使用免费图库 API（Pixabay、Pexels 等）
        if len(images) < count:
            images.extend(self._get_fallback_images(count - len(images), queries, date_str))

        return images[:count]

    def _search_unsplash(self, query: str) -> Optional[str]:
        """使用 Unsplash API 搜索图片"""
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
                "content_filter": "high"
            }
            response = requests.get(url, headers=headers, params=params, timeout=30)
            data = response.json()
            if data.get("results"):
                return data["results"][0]["urls"]["regular"]
        except Exception as e:
            print(f"Unsplash 搜索失败: {e}")
        return None

    def _download_image(self, url: str, query: str, date_str: str) -> Optional[str]:
        """下载图片到本地"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 生成文件名
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"{date_str}_{query_hash}.jpg"
            filepath = self.image_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return str(filepath)
        except Exception as e:
            print(f"图片下载失败: {e}")
            return None

    def _get_fallback_images(self, count: int, queries: List[str], date_str: str) -> List[str]:
        """备用图片获取方案 - 使用占位图服务或本地默认图"""
        images = []
        fallback_urls = [
            "https://picsum.photos/800/450",
            "https://picsum.photos/800/450?random=2",
            "https://picsum.photos/800/450?random=3"
        ]
        
        for i in range(count):
            url = fallback_urls[i % len(fallback_urls)]
            local_path = self._download_image(url, f"fallback_{i}", date_str)
            if local_path:
                images.append(local_path)
        
        return images

    def get_local_image_path(self, filename: str) -> str:
        """获取图片在构建后的相对路径"""
        return f"images/{filename}"


if __name__ == "__main__":
    finder = ImageFinder()
    queries = ["rocket space kids illustration", "children science experiment"]
    paths = finder.search_images(queries, count=2, date_str="2026-07-14")
    print(paths)
