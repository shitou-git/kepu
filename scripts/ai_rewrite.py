#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 改写模块 - 使用 AgensAI API 将科普内容改写成适合少年阅读的版本
"""

import os
import json
import requests
from typing import Optional


class AIWriter:
    def __init__(self):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        self.api_base = config["ai"]["api_base"]
        self.model = config["ai"]["model"]
        self.temperature = config["ai"]["temperature"]
        self.max_tokens = config["ai"]["max_tokens"]
        self.api_key = os.environ.get("AGENS_API_KEY", "")

    def _call_api(self, messages: list, temperature: Optional[float] = None) -> str:
        """调用 AgensAI API"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"API 调用失败: {e}")
            raise

    def generate_article(self, theme: str, theme_name: str, date_str: str) -> dict:
        """生成一篇科普文章"""
        system_prompt = """你是一位资深的少儿科普编辑，擅长为6-12岁的小学生创作生动有趣的科普文章。
你的文章特点：
1. 语言活泼、通俗易懂，多用比喻和拟人
2. 每段不要太长，适合小学生阅读
3. 多使用"你知道吗？""想象一下"等互动句式
4. 适当加入emoji增加趣味性
5. 文章结构清晰：标题→导语→正文（分3-4个小节）→知识小卡片→思考题
6. 字数控制在800字左右
7. 必须包含3-5个适合插入图片的场景描述"""

        user_prompt = f"""请为今日（{date_str}）的「{theme_name}」主题创作一篇科普文章。

主题要求：
- 主题：{theme_name}
- 面向：6-12岁小学生
- 风格：生动有趣、图文并茂、通俗易懂

请输出以下格式的内容（用 --- 分隔）：

TITLE: [文章标题]
---
SUMMARY: [50字以内的导语]
---
KEYWORDS: [3-5个关键词，用逗号分隔]
---
CONTENT:
[正文内容，使用 Markdown 格式，包含 ## 二级标题]
---
FACT_CARD:
[3-4条相关的趣味知识点，每条用 • 开头]
---
THINKING:
[2个引发思考的问题]
---
IMAGES:
[3个场景描述，用于搜索配图，每行一个描述，中英文都可]
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.85)
        return self._parse_article(result, theme, theme_name, date_str)

    def _parse_article(self, text: str, theme: str, theme_name: str, date_str: str) -> dict:
        """解析 AI 生成的文章"""
        parts = text.split("---")
        data = {
            "theme": theme,
            "theme_name": theme_name,
            "date": date_str,
            "title": "",
            "summary": "",
            "keywords": [],
            "content": "",
            "fact_card": [],
            "thinking": [],
            "image_prompts": []
        }

        for part in parts:
            part = part.strip()
            if part.startswith("TITLE:"):
                data["title"] = part.replace("TITLE:", "").strip()
            elif part.startswith("SUMMARY:"):
                data["summary"] = part.replace("SUMMARY:", "").strip()
            elif part.startswith("KEYWORDS:"):
                keywords = part.replace("KEYWORDS:", "").strip()
                data["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
            elif part.startswith("CONTENT:"):
                data["content"] = part.replace("CONTENT:", "").strip()
            elif part.startswith("FACT_CARD:"):
                lines = part.replace("FACT_CARD:", "").strip().split("\n")
                data["fact_card"] = [l.strip().lstrip("•- ") for l in lines if l.strip()]
            elif part.startswith("THINKING:"):
                lines = part.replace("THINKING:", "").strip().split("\n")
                data["thinking"] = [l.strip().lstrip("•- 0123456789.") for l in lines if l.strip()]
            elif part.startswith("IMAGES:"):
                lines = part.replace("IMAGES:", "").strip().split("\n")
                data["image_prompts"] = [l.strip() for l in lines if l.strip()]

        # 如果没有解析到图片提示，使用主题默认的
        if not data["image_prompts"]:
            data["image_prompts"] = [
                f"{theme_name} illustration for children",
                f"kids science education {theme}",
                f"colorful cartoon {theme} science"
            ]

        return data

    def rewrite_for_kids(self, raw_text: str, theme_name: str) -> str:
        """将已有内容改写成少年版"""
        system_prompt = """你是一位少儿科普编辑，请将提供的科普内容改写成适合6-12岁小学生阅读的文章。
要求：
1. 语言生动活泼，多用比喻、拟人
2. 段落简短，每段不超过3句话
3. 加入互动提问，引发思考
4. 保留核心知识点，去除过于学术的表达"""

        user_prompt = f"请将以下内容改写成「{theme_name}」主题的少儿科普文章：\n\n{raw_text}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self._call_api(messages)


if __name__ == "__main__":
    writer = AIWriter()
    article = writer.generate_article("aerospace", "航空航天", "2026-07-14")
    print(json.dumps(article, ensure_ascii=False, indent=2))
