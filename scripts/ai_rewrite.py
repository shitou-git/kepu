#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import time
import random
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
                print(f"API failed (retry {retry+1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(10 * (retry + 1))
        raise Exception(f"API failed after {max_retries} retries")

    def _build_storyteller_prompt(self) -> str:
        return """You are a teacher who has been telling science stories to children for ten years.
        
Your style:
- Tell science like storytelling, chatting with kids
- Start with a real life scene or a small suspense
- Mix short and long paragraphs for rhythm
- Exclaim at fun parts, explain slowly at deep parts
- Occasionally tell a scientist's anecdote or your childhood memory
- End by guiding children to observe and think

Writing principles:
1. Science must be accurate, verify data and years
2. Must connect to real life for understanding
3. Simple language suitable for 6-12 years old
4. No template openings like "Do you know" or "Imagine"
5. No formal phrases like "Therefore" or "In conclusion"
6. ABSOLUTELY NO filler words or verbal tics. Banned phrases include: 简单讲, 简单来说, 换句话说, 你会发现, 是不是, 说白了, 说实话, 你想想, 这么说吧, 讲真, 老实说, 其实吧, 其实呢, 众所周知, 毫无疑问, 显而易见, 不难发现, 事实上, 实际上, 总而言之, 综上所述, 由此可见. Just state the meaning directly without transitional filler words."""

    def generate_outline(self, theme_name: str, date_str: str, section_count: int = 3) -> Dict:
        system_prompt = self._build_storyteller_prompt()
        
        user_prompt = f"""Create an outline for a science article about "{theme_name}".

Theme scope guidance:
- "自然与动物" can cover: land animals, plants, marine life, ocean ecosystems, underwater creatures
- "宇宙探索" can cover: astronomy, stars, planets, spacecraft, satellites, space exploration
- "世界历史" can cover: ancient civilizations, historical events, famous historical figures
- "生命科学" can cover: human body, cells, DNA, health, growth, biological processes
- "科学创新" can cover: new technology, inventions, future tech, scientific breakthroughs
- "榜样人物" can cover: scientists, inventors, explorers, their stories and achievements

Requirements:
- Attractive title containing theme keywords
- Summary: one sentence with suspense or scene (within 50 chars)
- Exactly {section_count} section titles, each interesting
- One sentence description for each section

Output format:
TITLE: [title]
SUMMARY: [summary]
SECTIONS:
1. [section title 1]: [description]
2. [section title 2]: [description]
...
KEYWORDS: [3-5 keywords, comma separated]

IMPORTANT: Output exactly {section_count} sections. Use the exact format above."""

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

        lines = result.split("\n")
        in_sections = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.upper().startswith("TITLE:"):
                outline["title"] = line[len("TITLE:"):].strip().strip('"*')
            elif line.upper().startswith("SUMMARY:"):
                outline["summary"] = line[len("SUMMARY:"):].strip().strip('"*')
            elif line.upper().startswith("KEYWORDS:"):
                kw_line = line[len("KEYWORDS:"):].strip()
                outline["keywords"] = [k.strip() for k in re.split(r'[,，]', kw_line) if k.strip()]
                in_sections = False
            elif line.upper().startswith("SECTION"):
                in_sections = True
                continue
            elif re.match(r"^\d+[\.、]", line):
                in_sections = True
                match = re.match(r"^\d+[\.、]\s*(.+)", line)
                if match:
                    content = match.group(1).strip()
                    if ":" in content:
                        parts = content.split(":", 1)
                        title = parts[0].strip().strip('"*')
                        desc = parts[1].strip().strip('"*')
                        if title and desc:
                            outline["sections"].append({"title": title, "description": desc})
                    elif "：" in content:
                        parts = content.split("：", 1)
                        title = parts[0].strip().strip('"*')
                        desc = parts[1].strip().strip('"*')
                        if title and desc:
                            outline["sections"].append({"title": title, "description": desc})
            elif in_sections and line and not line.startswith("-") and not line.startswith("*"):
                pass

        if len(outline["sections"]) > section_count:
            outline["sections"] = outline["sections"][:section_count]

        return outline

    def generate_section(self, theme_name: str, section_title: str, section_desc: str,
                         outline_title: str, prev_section_text: str = "") -> str:
        system_prompt = self._build_storyteller_prompt()
        
        context = f"\nPrevious section reference: {prev_section_text[:200]}..." if prev_section_text else ""
        
        user_prompt = f"""Write a section for a science article about "{theme_name}".

Article title: {outline_title}
Section title: {section_title}
What to cover: {section_desc}

Requirements:
- 300-500 words, cover one knowledge point thoroughly
- Start with phenomenon/story, explain principle, connect to life
- Vivid language like chatting with kids
- Mix short and long paragraphs
- Put [IMAGE] marker at the end (on its own line)
- DO NOT include the section title in your output, only the body content

Output format:
[Content in Markdown, with [IMAGE] marker at end]""" + context

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.75)
        return result

    def generate_image_prompts(self, content: str, theme_name: str, image_count: int = 3) -> List[str]:
        system_prompt = """You are a professional children's science illustrator, skilled at creating precise image prompts.

Requirements:
1. Prompts must strictly correspond to specific scenes in the article
2. Include characters, actions, environment details
3. Style: watercolor hand-drawn, cartoon characters, Pixar animation style, bright colors, suitable for 6-12 years old
4. Absolutely no realistic human photos or portraits, use cartoon/illustration/animation style
5. English description, detailed and specific
6. No vague descriptions like "science illustration"

Output format: One prompt per line, corresponding to each [IMAGE] marker in order"""

        user_prompt = f"""Generate precise image prompts for {image_count} image markers based on the following article:

Article theme: {theme_name}

Article content:
{content}

Output {image_count} English image prompts, one per line."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.6)
        
        prompts = []
        for line in result.split("\n"):
            line = line.strip()
            if line and not line.startswith("---"):
                line = re.sub(r"^\d+[\.\)]\s*", "", line)
                prompts.append(line)
        
        return prompts[:image_count]

    def generate_fact_card(self, content: str, theme_name: str) -> List[str]:
        system_prompt = """You are a children's science editor, skilled at extracting interesting knowledge points.

Requirements:
1. Extract 3-4 interesting knowledge points from the article
2. Each point should be concise, contain numbers or unique trivia
3. Oral language, suitable for primary school students
4. Don't repeat article content, provide supplementary knowledge"""

        user_prompt = f"""Extract 3-4 interesting knowledge points from the following "{theme_name}" article:

{content}

Output format: One per line, starting with •"""

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
        system_prompt = """You are a teacher skilled at guiding children to think.

Requirements:
1. Ask 2 thought-provoking questions based on the article
2. Questions should be open-ended, encouraging observation, experiment or research
3. No standard answers, foster curiosity and exploration"""

        user_prompt = f"""Ask 2 thought-provoking questions based on the following "{theme_name}" article:

{content}

Output format: One question per line"""

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

    def generate_section_titles(self, sections_content: list, theme_name: str) -> list:
        section_count = len(sections_content)
        system_prompt = """You are a senior editor of children's science magazine, skilled at creating fun section titles.

Requirements:
1. Create a vivid and interesting title for each section based on content
2. Titles should attract kids, with curiosity or visual appeal
3. Each title no more than 15 characters
4. Lively style, use metaphors, personification, suspense
5. No dry titles like "Section 1" or "Part 1"""

        sections_text = ""
        for i, content in enumerate(sections_content, 1):
            sections_text += f"Section {i} content:\n{content[:300]}\n\n"

        user_prompt = f"""Create fun titles for {section_count} sections of a "{theme_name}" article:

{sections_text}
Output format: One title per line, {section_count} total, in order."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.7)
        
        titles = []
        for line in result.split("\n"):
            line = line.strip()
            if line:
                line = re.sub(r"^\d+[\.\)]\s*", "", line)
                line = line.strip('"「」『』')
                titles.append(line)
        
        return titles[:section_count]

    def generate_article(self, theme: str, theme_name: str, date_str: str) -> dict:
        section_count = random.randint(2, 4)
        print(f"  Random section count: {section_count}")
        
        print("  Step 1: Generating outline...")
        outline = None
        for attempt in range(3):
            outline = self.generate_outline(theme_name, date_str, section_count)
            if outline["title"] and len(outline["sections"]) >= 2:
                break
            print(f"    Outline incomplete (attempt {attempt+1}/3), retrying...")
            time.sleep(2)
        
        if not outline["title"] or len(outline["sections"]) < 2:
            raise Exception(f"Outline incomplete after 3 retries (got {len(outline['sections'])} sections)")
        
        actual_sections = len(outline["sections"])
        print(f"    Title: {outline['title']}")
        print(f"    Summary: {outline['summary']}")
        print(f"    Sections ({actual_sections}): {[s['title'] for s in outline['sections']]}")

        print(f"\n  Step 2: Generating content ({actual_sections} sections)...")
        sections_with_titles = []
        prev_text = ""
        
        for i, section in enumerate(outline["sections"], 1):
            print(f"    Generating section {i}: {section['title']}")
            text = self.generate_section(
                theme_name, section["title"], section["description"],
                outline["title"], prev_text
            )
            section_with_title = f"### {section['title']}\n\n{text}"
            sections_with_titles.append(section_with_title)
            prev_text = text

        content = outline["summary"] + "\n\n" + "\n\n".join(sections_with_titles)
        
        for i in range(1, actual_sections + 1):
            content = content.replace("[IMAGE]", f"[IMAGE_{i}]", 1)
        
        content = re.sub(r"(\S)\n\[IMAGE_", r"\1\n\n[IMAGE_", content)
        content = re.sub(r"\[IMAGE_(\d+)\]\n(\S)", r"[IMAGE_\1]\n\n\2", content)

        print("\n  Step 3: Generating image prompts...")
        image_prompts = self.generate_image_prompts(content, theme_name, actual_sections)
        print(f"    Image prompts ({len(image_prompts)}): {image_prompts}")

        print("\n  Step 4: Generating fact cards...")
        fact_card = self.generate_fact_card(content, theme_name)
        print(f"    Fact cards: {fact_card}")

        print("\n  Step 5: Generating thinking questions...")
        thinking = self.generate_thinking(content, theme_name)
        print(f"    Thinking questions: {thinking}")

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
            "image_prompts": image_prompts,
            "section_count": actual_sections
        }


if __name__ == "__main__":
    writer = AIWriter()
    article = writer.generate_article("aerospace", "航空航天", "2026-07-15")
    print("\n" + "="*60)
    print("Generated result:")
    print("="*60)
    print(json.dumps(article, ensure_ascii=False, indent=2))
