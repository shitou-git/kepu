#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 改写模块 - 使用 AgensAI API 将科普内容改写成适合少年阅读的版本
"""

import os
import json
import re
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

【最重要的原则】内容必须严谨准确：
1. 涉及真实人物时，必须准确核实其性别、身份、事迹，绝不能搞错性别（如屠呦呦是女性，不能称"爷爷""先生"等男性称谓）
2. 科学知识必须准确无误，数据、年份、原理等需基于事实
3. 必须包含科学知识在现实生活中的实际应用例子
4. 如果不确定某个事实，宁可不写也不要编造

文章特点：
1. 语言活泼、通俗易懂，多用比喻和拟人
2. 每段不要太长，适合小学生阅读
3. 多使用"你知道吗？""想象一下"等互动句式
4. 适当加入emoji增加趣味性
5. 文章结构清晰：导语→正文（分3个小节，每节有二级标题）→知识小卡片→思考题
6. 正文字数控制在1500字左右，内容要充实丰富，每个小节至少300字，深入展开知识点
7. 每个小节内必须包含1个图片标记 [IMAGE_N]，图片标记放在该小节段落的末尾
8. 图片提示词必须精确描述该小节的具体内容场景，而不是笼统的主题描述

【内容丰富度要求】
- 导语要生动引入，设置悬念或场景，激发阅读兴趣
- 每个小节要有完整的知识讲解：现象介绍→原理说明→实际应用→趣味拓展
- 多举生活中的具体例子，让孩子能联系实际
- 适当加入数据、对比、小实验等增强说服力
- 结尾要有情感升华或行动号召，引导孩子思考"""

        user_prompt = f"""请为今日（{date_str}）的「{theme_name}」主题创作一篇科普文章。

主题要求：
- 主题：{theme_name}
- 面向：6-12岁小学生
- 风格：生动有趣、图文并茂、通俗易懂
- 字数：正文1500字左右，内容充实，每个小节深入展开

【内容准确性要求】
- 涉及真实人物：必须使用正确的性别称谓，事迹必须准确
- 科学知识：原理、数据、年份必须基于事实，不可编造
- 实际应用：正文中必须包含该科学知识在现实生活中的应用实例
- 称谓使用：男性用"爷爷/叔叔/哥哥"，女性用"奶奶/阿姨/姐姐"，不可混淆

【内容丰富度要求】
- 每个小节至少300字，包含：现象/背景介绍、原理讲解、生活应用、趣味拓展
- 多用具体的生活实例和数据，避免空洞描述
- 每个小节层层递进，讲透一个知识点

请输出以下格式的内容（用 --- 分隔）：

TITLE: [文章标题]
---
SUMMARY: [50字以内的导语]
---
KEYWORDS: [3-5个关键词，用逗号分隔]
---
CONTENT:
[正文内容，使用标准 Markdown 格式：
- ## 二级标题
- **加粗文字**
- *斜体文字*
- 导语段落后放 [IMAGE_1]，图片描绘导语中提到的核心人物或场景
- 第1个小节末尾放 [IMAGE_2]，图片描绘该小节具体描述的场景
- 第2个小节末尾放 [IMAGE_3]，图片描绘该小节具体描述的场景
- 每个图片标记独占一行，放在段落文字之后
- 正文总字数1500字左右，每个小节至少300字]
---
FACT_CARD:
[3-4条相关的趣味知识点，每条用 • 开头]
---
THINKING:
[2个引发思考的问题]
---
IMAGE_PROMPTS:
[3个图片提示词，分别对应 [IMAGE_1]、[IMAGE_2]、[IMAGE_3]，每行一个，英文描述]
重要要求：
- IMAGE_1 的提示词必须描述导语中提到的核心人物或事物
- IMAGE_2 的提示词必须描述第1个小节具体讲述的场景
- IMAGE_3 的提示词必须描述第2个小节具体讲述的场景
- 提示词要具体、可视化，包含人物、动作、环境细节
- 涉及真实人物时，提示词中需注明人物性别特征
- 风格：儿童科普插画风格，色彩鲜明，适合6-12岁儿童
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
            elif part.startswith("IMAGE_PROMPTS:"):
                lines = part.replace("IMAGE_PROMPTS:", "").strip().split("\n")
                data["image_prompts"] = [re.sub(r'^\d+[\.\)]\s*', '', l.strip()) for l in lines if l.strip()]
            elif part.startswith("IMAGES:"):
                lines = part.replace("IMAGES:", "").strip().split("\n")
                data["image_prompts"] = [re.sub(r'^\d+[\.\)]\s*', '', l.strip()) for l in lines if l.strip()]

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
