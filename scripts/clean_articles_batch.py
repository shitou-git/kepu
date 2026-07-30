#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量清洗文章：禁用口语 + 正文混英文 + fact_card 英文。
运行后会原地修改 content/archives/*.json，并打印改动摘要。
"""

import json
import re
from pathlib import Path

# 禁用口语 → 替换策略（保留原意去掉语气词）
BANNED_REPLACEMENTS = [
    # 整句开头语气词
    ("小朋友们，你们知道吗？在", "在"),
    ("你们知道吗？早在", "早在"),
    ("你们知道吗？现在", "现在"),
    ("你知道吗？这种", "这种"),
    ("你知道吗？这种", "这种"),
    ("你知道吗？", ""),
    ("你们知道吗？", ""),
    # 句中/句末
    ("下次当你看到地图上的线条和符号时，不妨想想：这些看似普通的标记背后，藏着多少人类智慧的结晶呢？",
     "下次当你看到地图上的线条和符号时，可以思考：这些看似普通的标记背后，藏着多少人类智慧的结晶。"),
    ("下次当你洗澡时，不妨想一想阿基米德的“尤里卡”时刻，或者在夜晚仰望星空时，想起古希腊天文学家们的探索",
     "下次当你洗澡时，可以想想阿基米德的“尤里卡”时刻，或者在夜晚仰望星空时，想起古希腊天文学家们的探索"),
    ("下次你抬头看星星的时候，可以想一想：那些闪烁的光点后面，是不是也有什么在看着我们？",
     "下次你抬头看星星的时候，不妨思考：那些闪烁的光点后面，是不是也有什么在看着我们？"),
    ("下次你看到植物在太阳下伸展叶子时，可以想一想，它们是不是正在开心地喝彩色水呢？",
     "下次你看到植物在太阳下伸展叶子时，不妨观察，它们是不是正在开心地喝彩色水。"),
    ("想象一下，你玩跷跷板时，只要位置对，轻轻一跳就能把很重的小伙伴翘起来。",
     "就像玩跷跷板，只要位置对，轻轻一跳就能把很重的小伙伴翘起来。"),
    ("想象一下，如果没有这些聪明的设计，金字塔怎么可能那么稳固，屹立了四千多年？",
     "如果没有这些聪明的设计，金字塔不可能那么稳固，屹立四千多年。"),
    ('想象一下，如果你在海上放一张巨大的帆，风吹过来船就能前进。科学家们在太空中也放了',
     '就像在海上放一张巨大的帆，风吹过来船就能前进。科学家们在太空中也放了'),
    ("你有没有好奇过，", ""),
    ("晚上拧开台灯那一下，你有没有好奇过，这束光是怎么从黑暗里“逃”出来的？",
     "晚上拧开台灯那一下，也许你会好奇，这束光是怎么从黑暗里“逃”出来的。"),
]

# 正文英文 → 中文映射（科学专有名词保留括号里的英文是允许的，这里主要处理纯英文描述）
ENGLISH_REPLACEMENTS = [
    # twisted ladder
    ("或者说是 twisted ladder", "或者说是“扭拧的梯子”"),
    # tiny 的工人
    ("无数种 tiny 的“工人”", "无数种微小的“工人”"),
    # conquered 了波斯
    (" conquered 了", "征服了"),
    # hitchhiker（搭便车者）
    ('是森林里的“ hitchhiker”（搭便车者）。', '是森林里的“搭便车者”（hitchhiker）。'),
    # immune 相关：neutrophils / monocytes / macrophages / lymphocytes / antibodies
    ("neutrophils（中性粒细胞）", "中性粒细胞（neutrophils）"),
    ("monocytes（单核细胞）", "单核细胞（monocytes）"),
    ("macrophages（巨噬细胞）", "巨噬细胞（macrophages）"),
    ("lymphocytes（淋巴细胞）", "淋巴细胞（lymphocytes）"),
    ("antibodies（抗体）", "抗体（antibodies）"),
    # Planetes（漫游者）
    ("“Planetes”，意思是“漫游者”。这就是现在的行星，比如火星或木星。",
     "“漫游者”。这就是现在的行星，比如火星或木星。"),
    # Wood Wide Web 处理：前后文已经给了中文“木维网”，保留但整理顺序
    ("我们叫它“木维网”（Wood Wide Web）。", "我们叫它“木维网”（Wood Wide Web，全球树木互联网络）。"),
    # Europa / Enceladus（卫星名，正常专有名词，保留）
]

# 2026-07-28_1 fact_card 全英文 → 中文翻译
FACTCARD_EN_28_1 = [
    "大象大脑里有一块特殊的区域叫做“颞叶”，能帮助它们记上几十年的事情——比如十年大旱之后再找到水源，这种记忆力是不是很惊人？",
    "蜜蜂对授粉至关重要，没有它们，苹果树结的果子又少又小；科学家发现加入蜜蜂授粉，果实产量可以翻倍！",
    "在美国黄石国家公园，重新引入狼之后，鹿的数量得到控制，森林和河流都恢复了生机——这就是一种动物如何改变整个生态系统的完美例子。",
    "就连蚯蚓这样的小生物也扮演着巨大角色——它们翻动土壤让土质更肥沃，帮助植物的根长得粗壮又健康。",
]


def clean_text(text: str) -> str:
    if not text:
        return text
    for a, b in BANNED_REPLACEMENTS + ENGLISH_REPLACEMENTS:
        text = text.replace(a, b)
    return text


def main():
    total = 0
    changed_files = []
    for f in sorted(Path("content/archives").glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  读取失败 {f.name}: {e}")
            continue

        before = json.dumps(d, ensure_ascii=False)

        for key in ("summary", "content"):
            d[key] = clean_text(d.get(key, ""))

        for arr_key in ("fact_card", "thinking"):
            arr = d.get(arr_key) or []
            d[arr_key] = [clean_text(x) for x in arr]

        # 特殊处理：2026-07-28_1 的 fact_card 整体替换
        if f.name == "2026-07-28_1.json":
            d["fact_card"] = FACTCARD_EN_28_1[:]

        after = json.dumps(d, ensure_ascii=False)

        if before != after:
            total += 1
            changed_files.append(f.name)
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"共修改 {total} 篇文章:")
    for n in changed_files:
        print(f"  - {n}")


if __name__ == "__main__":
    main()
