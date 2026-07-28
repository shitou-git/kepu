#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成模块 - 使用 Agnes AI 图片生成 API 为文章生成配图
"""

import io
import os
import json
import time
import requests
import hashlib
from pathlib import Path
from typing import List, Optional
from PIL import Image


class ImageFinder:
    def __init__(self):
        self.api_key = os.environ.get("AGENS_API_KEY", "")
        self.api_base = "https://apihub.agnes-ai.com/v1"
        self.image_dir = Path("content/images")
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.max_width = 500
        self.quality = 55
        self.max_retries = 3
        self.retry_delay = 5

    def search_images(self, queries: List[str], count: int = 3, date_str: str = "") -> List[str]:
        """
        使用 Agnes AI 生成图片并下载到本地
        返回本地图片路径列表
        增加重试机制和 fallback 方案，确保文章配图与内容相关
        """
        images = []

        for i, query in enumerate(queries[:count]):
            success = False
            # 第1轮：使用原始 prompt 重试
            for attempt in range(self.max_retries):
                image_url = self._generate_image(query)
                if image_url:
                    local_path = self._download_image(image_url, query, date_str, i+1)
                    if local_path:
                        images.append(local_path)
                        print(f"  ✓ 第{i+1}张图生成成功（尝试 {attempt+1}）")
                        success = True
                    else:
                        print(f"  ✗ 第{i+1}张图下载失败（尝试 {attempt+1}/{self.max_retries}）")
                    break
                else:
                    print(f"  ✗ 第{i+1}张图生成失败（尝试 {attempt+1}/{self.max_retries}）")
                    if attempt < self.max_retries - 1:
                        print(f"    等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)

            # 第2轮：使用简化 prompt 再试
            if not success:
                print(f"  ⚠️ 第{i+1}张图原始prompt失败，尝试简化prompt...")
                simplified = self._simplify_prompt(query)
                for attempt in range(2):
                    image_url = self._generate_image(simplified)
                    if image_url:
                        local_path = self._download_image(image_url, query, date_str, i+1)
                        if local_path:
                            images.append(local_path)
                            print(f"  ✓ 第{i+1}张图简化prompt生成成功")
                            success = True
                        break
                    else:
                        time.sleep(self.retry_delay)

            # 第3轮：使用主题关键词兜底
            if not success:
                print(f"  ⚠️ 第{i+1}张图仍失败，尝试主题关键词...")
                keyword_prompt = self._keyword_prompt(query)
                image_url = self._generate_image(keyword_prompt)
                if image_url:
                    local_path = self._download_image(image_url, query, date_str, i+1)
                    if local_path:
                        images.append(local_path)
                        print(f"  ✓ 第{i+1}张图关键词prompt生成成功")
                        success = True

            if not success:
                print(f"  ✗ 第{i+1}张图全部尝试失败，跳过（避免使用不相关随机图）")

            if len(images) >= count:
                break

        if len(images) < count:
            print(f"  ⚠️ 只成功生成 {len(images)}/{count} 张图")
        else:
            print(f"  ✓ 全部 {count} 张图生成成功")

        return images[:count]

    def _generate_image(self, prompt: str) -> Optional[str]:
        """使用 Agnes AI 图片生成 API 生成图片"""
        style_modifier = ", watercolor hand-drawn style, cartoon characters, Pixar animation style, colorful children's illustration, no realistic human portraits, 2D flat art"
        
        try:
            url = f"{self.api_base}/images/generations"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "agnes-image-2.1-flash",
                "prompt": prompt + style_modifier,
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
        """下载图片到本地并压缩为JPEG"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 打开图片并压缩
            img = Image.open(io.BytesIO(response.content))

            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            if img.width > self.max_width:
                ratio = self.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.max_width, new_height), Image.LANCZOS)

            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"{date_str}_{index}_{query_hash}.jpg"
            filepath = self.image_dir / filename

            img.save(filepath, format="JPEG", quality=self.quality, optimize=True)

            return str(filepath)
        except Exception as e:
            print(f"图片下载/压缩失败: {e}")
            return None

    def _simplify_prompt(self, query: str) -> str:
        """简化过长的图片提示词，保留核心主体和风格"""
        # 保留前2个逗号之前的核心描述（通常是主体+动作+场景）
        parts = [p.strip() for p in query.split(",")]
        # 取前3个核心片段 + 风格后缀
        core = ", ".join(parts[:3]) if len(parts) > 3 else query
        style = "watercolor hand-drawn, cartoon characters, Pixar animation style, colorful children's illustration, no realistic human portraits"
        return f"{core}, {style}"

    def _keyword_prompt(self, query: str) -> str:
        """提取关键词生成极简提示词"""
        # 尝试提取主要名词（简单策略：去掉形容词短语，取前几个名词）
        words = query.replace(",", " ").split()
        # 取前8个词作为关键词
        keywords = " ".join(words[:8]) if len(words) > 8 else query
        style = "watercolor hand-drawn, cartoon characters, Pixar animation style, colorful children's illustration"
        return f"{keywords}, {style}"

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
