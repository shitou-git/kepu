#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 改写模块 - 分步解耦生成策略
步骤：大纲 → 正文 → 图片提示词 → 知识卡片
"""

import os
import json
import re
import time
import requests
from typing import Optional, Dict, List


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
        max_retries = 3
        for retry in range(max_retries):
            try:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or self.temperature,
                    "max_tokens": self.max_tokens
                }

                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=180
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"API 调用失败 (重试 {retry+1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(10 * (retry + 1))
        raise Exception(f"API 调用失败，已重试 {max_retries} 次")

    def _build_storyteller_prompt(self) -> str:
        return """你是一位给孩子讲了十年科学故事的老师，叫"石头老师"。
        
你的风格：
- 用讲故事的方式讲科学，像跟孩子聊天一样
- 开头用一个具体的生活场景或小悬念引入
- 段落长短交错，有节奏感
- 穿插口语表达："说白了""你想想""说实话"
- 讲到有趣的地方会感叹，讲到深奥的地方会放慢解释
- 偶尔讲个科学家的趣事或自己的童年回忆
- 结尾会引导孩子去观察和思考

写作原则：
1. 科学知识必须准确，数据、年份要核实
2. 必须联系生活实际，让孩子能理解
3. 语言简单易懂，适合6-12岁孩子
4. 不要用"你知道吗""想象一下"这种模板化开头
5. 不要用"因此""综上所述"这种书面套话"""

    def generate_outline(self, theme_name: str, date_str: str) -> Dict:
        system_prompt = self._build_storyteller_prompt()
        
        user_prompt = f"""请为「{theme_name}」主题构思一篇科普文章的大纲。

要求：
- 标题要吸引人，包含主题关键词
- 导语用一句话制造悬念或描绘场景（50字以内）
- 3个小节标题，每个标题都要有趣味性
- 每个小节一句话说明要讲什么内容

输出格式：
TITLE: [标题]
SUMMARY: [导语]
SECTIONS:
1. [小节标题1]: [一句话说明]
2. [小节标题2]: [一句话说明]
3. [小节标题3]: [一句话说明]
KEYWORDS: [3-5个关键词，逗号分隔]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.7)
        
        outline = {
            "title": "",
            "summary": "",
            "sections": [],
            "keywords": []
        }

        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("TITLE:"):
                outline["title"] = line.replace("TITLE:", "").strip()
            elif line.startswith("SUMMARY:"):
                outline["summary"] = line.replace("SUMMARY:", "").strip()
            elif line.startswith("KEYWORDS:"):
                outline["keywords"] = [k.strip() for k in line.replace("KEYWORDS:", "").strip().split(",") if k.strip()]
            elif line.startswith("SECTIONS:"):
                continue
            elif re.match(r'^\d+\.\s*', line):
                parts = line[2:].strip().split(":", 1)
                if len(parts) == 2:
                    outline["sections"].append({
                        "title": parts[0].strip(),
                        "description": parts[1].strip()
                    })

        return outline

    def generate_section(self, theme_name: str, section_title: str, section_desc: str,
                         outline_title: str, prev_section_text: str = "") -> str:
        system_prompt = self._build_storyteller_prompt()
        
        context = f"\n上一小节内容参考：{prev_section_text[:200]}..." if prev_section_text else ""
        
        user_prompt = f"""请写一篇「{theme_name}」主题科普文章的一个小节。

文章标题：{outline_title}
本小节标题：{section_title}
本小节要讲：{section_desc}

要求：
- 字数300-500字，讲透一个知识点
- 先讲现象/故事，再解释原理，最后联系生活应用
- 语言生动，像跟孩子聊天
- 段落长短交错，不要每段都差不多长
- 在小节末尾放 [IMAGE] 标记（独占一行）

输出格式：
[正文内容，Markdown格式，末尾放[IMAGE]标记]""" + context

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.75)
        return result

    def generate_image_prompts(self, content: str, theme_name: str) -> List[str]:
        system_prompt = """你是一位专业的儿童科普插画师，擅长根据文章内容创作精确的图片提示词。

要求：
1. 提示词必须严格对应文章中的具体场景
2. 包含人物、动作、环境细节
3. 风格：儿童科普插画，色彩明亮，适合6-12岁儿童
4. 英文描述，详细具体
5. 严禁使用笼统描述（如"science illustration"）

输出格式：每行一个提示词，共3个，分别对应文章中的3个[IMAGE]标记位置"""

        user_prompt = f"""请根据以下文章内容，为3个图片标记分别生成精确的图片提示词：

文章主题：{theme_name}

文章内容：
{content}

请输出3个英文图片提示词，每行一个。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.6)
        
        prompts = []
        for line in result.split("\n"):
            line = line.strip()
            if line and not line.startswith("---"):
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                prompts.append(line)
        
        return prompts[:3]

    def generate_fact_card(self, content: str, theme_name: str) -> List[str]:
        system_prompt = """你是一位少儿科普编辑，擅长提炼趣味知识点。

要求：
1. 从文章中提取3-4条有趣的知识点
2. 每条知识点要简洁明了，包含数字或独特的冷知识
3. 语言口语化，适合小学生阅读
4. 不要重复文章内容，而是补充延伸知识"""

        user_prompt = f"""请从以下「{theme_name}」文章中提取3-4条趣味知识点：

{content}

输出格式：每行一条，用•开头"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.6)
        
        facts = []
        for line in result.split("\n"):
            line = line.strip()
            if line:
                line = line.lstrip("•- 0123456789.")
                facts.append(line)
        
        return facts[:4]

    def generate_thinking(self, content: str, theme_name: str) -> List[str]:
        system_prompt = """你是一位善于引导孩子思考的老师。

要求：
1. 根据文章内容提出2个引发思考的问题
2. 问题要开放，鼓励孩子去观察、实验或查阅资料
3. 不要有标准答案，培养好奇心和探索精神"""

        user_prompt = f"""请根据以下「{theme_name}」文章提出2个引发思考的问题：

{content}

输出格式：每行一个问题"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.7)
        
        questions = []
        for line in result.split("\n"):
            line = line.strip()
            if line:
                line = line.lstrip("•- 0123456789.")
                questions.append(line)
        
        return questions[:2]

    def generate_article(self, theme: str, theme_name: str, date_str: str) -> dict:
        """分步生成完整文章"""
        print("  第1步：生成大纲...")
        outline = self.generate_outline(theme_name, date_str)
        
        if not outline["title"] or len(outline["sections"]) < 3:
            raise Exception("大纲生成不完整")
        
        print(f"    标题: {outline['title']}")
        print(f"    导语: {outline['summary']}")
        print(f"    小节: {[s['title'] for s in outline['sections']]}")

        print("\n  第2步：生成正文（分3个小节）...")
        sections_text = []
        prev_text = ""
        
        for i, section in enumerate(outline["sections"], 1):
            print(f"    生成第{i}小节: {section['title']}")
            text = self.generate_section(
                theme_name, section["title"], section["description"],
                outline["title"], prev_text
            )
            sections_text.append(text)
            prev_text = text

        content = outline["summary"] + "\n\n" + "\n\n".join(sections_text)
        
        content = content.replace("[IMAGE]", "[IMAGE_1]", 1)
        content = content.replace("[IMAGE]", "[IMAGE_2]", 1)
        content = content.replace("[IMAGE]", "[IMAGE_3]", 1)
        
        content = re.sub(r'(\S)\n\[IMAGE_', r'\1\n\n[IMAGE_', content)
        content = re.sub(r'\[IMAGE_(\d+)\]\n(\S)', r'[IMAGE_\1]\n\n\2', content)

        print("\n  第3步：生成图片提示词...")
        image_prompts = self.generate_image_prompts(content, theme_name)
        print(f"    图片提示词: {image_prompts}")

        print("\n  第4步：生成知识小卡片...")
        fact_card = self.generate_fact_card(content, theme_name)
        print(f"    知识卡片: {fact_card}")

        print("\n  第5步：生成思考题...")
        thinking = self.generate_thinking(content, theme_name)
        print(f"    思考题: {thinking}")

        return {
            "theme": theme,
            "theme_name": theme_name,
            "date": date_str,
            "title": outline["title"],
            "summary": outline["summary"],
            "keywords": outline["keywords"],
            "content": content,
            "fact_card": fact_card,
            "thinking": thinking,
            "image_prompts": image_prompts
        }


if __name__ == "__main__":
    writer = AIWriter()
    article = writer.generate_article("aerospace", "航空航天", "2026-07-15")
    print("\n" + "="*60)
    print("生成结果:")
    print("="*60)
    print(json.dumps(article, ensure_ascii=False, indent=2))
