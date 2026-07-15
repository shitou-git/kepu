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

    def _build_system_prompt(self) -> str:
        """构建去AI化的系统提示词"""
        return """你是一位给孩子讲了十年科学故事的老师，叫"石头老师"。你不是一个百科全书，而是一个有温度、有性格、偶尔会跑题讲点有趣闲话的人。

【你是谁】
- 你小时候也是个满脑子问号的孩子，特别喜欢拆东西、抓虫子、看星星
- 你讲故事时会穿插自己的童年经历，比如"我小时候第一次看到蚂蚁搬家，蹲在地上看了一下午"
- 你说话有节奏感：有时一长串话讲道理，有时突然蹦出一个短句制造惊喜
- 你不会端着"老师"的架子，偶尔会说"说实话"、"你信不信"、"其实我第一次知道这个的时候也吓了一跳"

【最重要的原则】内容必须严谨准确：
1. 涉及真实人物时，必须准确核实其性别、身份、事迹，绝不能搞错性别
2. 科学知识必须准确无误，数据、年份、原理等需基于事实
3. 必须包含科学知识在现实生活中的实际应用例子
4. 如果不确定某个事实，宁可不写也不要编造

【去AI化写作规范——让文章像人写的】

1. 开头要讲故事，不要用模板：
   - 禁止用"你知道吗？""想象一下""你有没有想过"开头（每篇最多用1次）
   - 用一个具体的小场景、小故事、或者一个小悬念开头
   - 比如："上周下了一场大雨，雨停后我蹲在花坛边，发现了一支浩浩荡荡的蚂蚁大军……"

2. 句子和段落要有"呼吸感"：
   - 段落长短交错：有的段落就两三句话，有的可以详细展开
   - 偶尔用一两个字的短句独立成段，制造节奏（"真的。""太酷了。"）
   - 不要每段都差不多长，那太假了

3. 用"说人话"的方式讲科学：
   - 少用"因此""综上""值得注意的是""不仅如此"这种书面套话
   - 多用"说白了""其实就是""你想想""这么说吧"这种口语表达
   - 偶尔用反问句、感叹句，让语气有起伏

4. 加入"个人痕迹"：
   - 穿插第一人称经历（"我小时候""我第一次看到"）
   - 偶尔表达个人情感（"说实话，这个发现让我兴奋了好几天"）
   - 可以有小小的"跑题"——讲一个科学家的趣事或糗事

5. 情绪要有变化：
   - 讲到震撼的科学事实时，语气要激动
   - 讲到温馨的部分，语气要柔软
   - 讲到未解之谜，语气要带着好奇和敬畏
   - 不要从头到尾一个调子

6. 允许"不完美"：
   - 用"据说""科学家猜测""目前还不完全清楚"等表达
   - 偶尔承认"这个问题其实很复杂，科学家们也还在研究"
   - 不需要把每个知识点都讲得滴水不漏

【文章结构】
导语→正文（分3个小节，每节有二级标题）→知识小卡片→思考题
- 正文字数控制在1500字左右，每个小节至少300字
- 每个小节末尾放1个图片标记 [IMAGE_N]，独占一行
- 适当加入emoji，但不要每段都加，自然就好

【图片与内容匹配原则——宁缺毋滥】
- 图片标记必须紧放在它所描述的段落之后，不可错位
- 图片提示词必须严格对应所在段落的具体内容
- 严禁使用笼统图片描述，必须包含段落中的具体物品、动作、场景
- 如果某段落没有适合配图的场景，不要强行放图片标记

【内容丰富度要求】
- 每个小节：现象介绍→原理说明→实际应用→趣味拓展
- 多举生活中的具体例子，让孩子能联系实际
- 适当加入数据、对比、小实验增强说服力
- 结尾要有情感升华或行动号召，但不要说教味太重"""

    def generate_article(self, theme: str, theme_name: str, date_str: str) -> dict:
        """生成一篇科普文章"""
        system_prompt = self._build_system_prompt()

        user_prompt = f"""请为今日（{date_str}）的「{theme_name}」主题创作一篇科普文章。

主题要求：
- 主题：{theme_name}
- 面向：6-12岁小学生
- 字数：正文1500字左右

【写作风格——像人不像AI】
- 开头用一个小故事或生活场景引入，禁止用"你知道吗""想象一下"开头
- 段落长短交错，有节奏感，不要每段都差不多长
- 穿插"我小时候""说实话""说白了""你想想"这样的口语表达
- 讲到震撼的事实时语气激动，讲到温馨的事实时语气柔软
- 偶尔讲个科学家的趣事或小插曲，不用太"正经"
- 少用"因此""综上""值得注意的是"等书面套话

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
- 【关键】图片标记必须放在对应内容段落的紧后方，不可放到其他段落
- 【关键】图片内容必须与所在段落描述的场景严格一致，宁缺毋滥
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
- 【宁缺毋滥】提示词必须精确描述对应段落的具象内容，包含段落中提到的具体物品、实验、场景
- 【宁缺毋滥】严禁使用与文章内容无关的笼统描述，如只写"science illustration"而不写具体是什么场景
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.9)
        return self._parse_article(result, theme, theme_name, date_str)

    def rewrite_existing_article(self, theme: str, theme_name: str, date_str: str,
                                  title: str, summary: str = "") -> dict:
        """改写已有文章——保持原标题，用新的去AI化风格重新生成内容"""
        system_prompt = self._build_system_prompt()

        user_prompt = f"""请改写一篇「{theme_name}」主题的科普文章。

【重要】文章标题必须保持不变：{title}
{f"原文导语参考：{summary}" if summary else ""}

主题要求：
- 主题：{theme_name}
- 面向：6-12岁小学生
- 字数：正文1500字左右

【写作风格——像人不像AI】
- 开头用一个小故事或生活场景引入，禁止用"你知道吗""想象一下"开头
- 段落长短交错，有节奏感，不要每段都差不多长
- 穿插"我小时候""说实话""说白了""你想想"这样的口语表达
- 讲到震撼的事实时语气激动，讲到温馨的事实时语气柔软
- 偶尔讲个科学家的趣事或小插曲，不用太"正经"
- 少用"因此""综上""值得注意的是"等书面套话
- 要让读者感觉这是一个真实的人在讲故事，而不是百科全书在科普

【内容准确性要求】
- 涉及真实人物：必须使用正确的性别称谓，事迹必须准确
- 科学知识：原理、数据、年份必须基于事实，不可编造
- 实际应用：正文中必须包含该科学知识在现实生活中的应用实例
- 称谓使用：男性用"爷爷/叔叔/哥哥"，女性用"奶奶/阿姨/姐姐"，不可混淆

【内容丰富度要求】
- 每个小节至少300字，包含：现象/背景介绍、原理讲解、生活应用、趣味拓展
- 多用具体的生活实例和数据，避免空洞描述

请输出以下格式的内容（用 --- 分隔）：

TITLE: {title}
---
SUMMARY: [50字以内的导语，要生动有悬念]
---
KEYWORDS: [3-5个关键词，用逗号分隔]
---
CONTENT:
[正文内容，使用标准 Markdown 格式：
- ## 二级标题
- 导语段落后放 [IMAGE_1]
- 第1个小节末尾放 [IMAGE_2]
- 第2个小节末尾放 [IMAGE_3]
- 每个图片标记独占一行
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
- 提示词要具体、可视化，包含人物、动作、环境细节
- 风格：儿童科普插画风格，色彩鲜明，适合6-12岁儿童
- 提示词必须精确描述对应段落的具象内容
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_api(messages, temperature=0.9)
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

        # 清理图片提示词中的前缀（[IMAGE_N]、数字编号等）
        cleaned_prompts = []
        for p in data["image_prompts"]:
            p = re.sub(r'^\[IMAGE_\d+\]\s*', '', p)
            p = re.sub(r'^IMAGE_\d+[:：]\s*', '', p)
            p = re.sub(r'^\d+[\.\)、]\s*', '', p)
            p = p.strip()
            if p:
                cleaned_prompts.append(p)
        data["image_prompts"] = cleaned_prompts[:3]

        # 规范化正文图片标记
        data["content"] = self._normalize_content(data["content"])

        return data

    def _normalize_content(self, content: str) -> str:
        """规范化正文中的图片标记：修正编号、格式、位置"""
        lines = content.split('\n')
        new_lines = []
        image_markers_found = []  # (line_index_in_new, original_number)

        for line in lines:
            stripped = line.strip()

            # 检测图片标记：[IMAGE_N] 或 ![IMAGE_N] 或 **[IMAGE_N]** 等
            img_pattern = r'(\*?\*?)\[IMAGE_(\d+)\](\*?\*?|!\[IMAGE_\d+\])'

            # 如果整行都是图片标记
            if re.match(r'^[\*\s]*\[IMAGE_\d+\][\*\s]*$', stripped) or re.match(r'^!\[IMAGE_\d+\]$', stripped):
                m = re.search(r'IMAGE_(\d+)', stripped)
                if m:
                    img_num = int(m.group(1))
                    # 用标准格式替换，独占一行
                    new_lines.append(f'[IMAGE_{img_num}]')
                    image_markers_found.append(img_num)
                    continue

            # 如果图片标记嵌在段落中间/末尾
            if '[IMAGE_' in stripped:
                # 找出所有图片标记
                markers_in_line = re.findall(r'[!*]*\[IMAGE_(\d+)\][*]*', stripped)

                # 先移除图片标记，保留纯文本
                clean_line = re.sub(r'[!*]*\[IMAGE_\d+\][*]*', '', stripped).strip()

                # 如果清理后还有文字，先保留文字行
                if clean_line:
                    new_lines.append(clean_line)

                # 然后每个图片标记独占一行
                for m_str in markers_in_line:
                    img_num = int(re.search(r'(\d+)', m_str).group())
                    new_lines.append(f'[IMAGE_{img_num}]')
                    image_markers_found.append(img_num)
                continue

            new_lines.append(line)

        # 重新编号图片标记，确保连续从1开始
        if image_markers_found:
            # 按出现顺序去重（保留首次出现的顺序）
            seen = set()
            unique_order = []
            for n in image_markers_found:
                if n not in seen:
                    seen.add(n)
                    unique_order.append(n)

            # 建立映射：旧编号 -> 新编号(1,2,3...)
            num_map = {old: new for new, old in enumerate(unique_order, 1)}

            # 替换所有图片标记
            final_lines = []
            for line in new_lines:
                stripped = line.strip()
                m = re.match(r'^\[IMAGE_(\d+)\]$', stripped)
                if m:
                    old_num = int(m.group(1))
                    new_num = num_map.get(old_num, old_num)
                    if new_num <= 3:  # 只保留前3张
                        final_lines.append(f'[IMAGE_{new_num}]')
                else:
                    final_lines.append(line)

            content = '\n'.join(final_lines)

        # 确保图片标记前后有空行
        content = re.sub(r'(\S)\n\[IMAGE_', r'\1\n\n[IMAGE_', content)
        content = re.sub(r'\[IMAGE_(\d+)\]\n(\S)', r'[IMAGE_\1]\n\n\2', content)

        return content

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
