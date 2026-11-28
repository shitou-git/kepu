#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成全站汉字组词 / 成语静态词典：data/word_dict.json

设计目标：
- 运行时不再依赖 Cloudflare Worker（旧模型下线 + 429），文章页直接读取静态 JSON。
- 组词由 AI 批量生成，并用 jieba 词频过滤生造词。
- 成语从公开的汉语成语词典校验（https://github.com/pwxcoo/chinese-xinhua），避免 AI 编造。
- 已生成的汉字会保留，支持增量更新；失败批次会重试，不会静默吞掉错误。

本地：AGENS_API_KEY 放 .env；线上：GitHub Actions Secrets。
用法：
    python scripts/build_word_dict.py                 # 生成全部缺失汉字
    python scripts/build_word_dict.py --limit 120     # 只补最近新增的 120 个字
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from env_loader import require_api_key  # noqa: E402

HANZI = re.compile(r"[\u4e00-\u9fff]")


def is_hanzi_string(text):
    return bool(text) and all(HANZI.fullmatch(ch) for ch in text)
IDIOM_URL = "https://cdn.jsdelivr.net/gh/pwxcoo/chinese-xinhua@master/data/idiom.json"
IDIOM_CACHE = Path(tempfile.gettempdir()) / "kepu_idiom_dict.json"
DICT_PATH = ROOT / "data" / "word_dict.json"
CONFIG_PATH = ROOT / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_chars():
    """收集所有文章中出现过的汉字（含标题、正文、知识卡、思考题、关键词）。"""
    chars = set()
    for path in sorted((ROOT / "content" / "archives").glob("*.json")):
        try:
            art = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"跳过损坏文章 {path.name}: {exc}")
            continue
        parts = [art.get("title", ""), art.get("content", "")]
        parts += art.get("fact_card", []) or []
        parts += art.get("thinking", []) or []
        parts += art.get("keywords", []) or []
        for text in parts:
            if isinstance(text, str):
                chars.update(HANZI.findall(text))
    return sorted(chars)


def load_word_freq():
    """读取 jieba 词频表，用于过滤 AI 生造词。缺失时退化为只做结构校验。"""
    try:
        import jieba  # noqa: F401
        import jieba as _jieba_module
        dict_path = Path(_jieba_module.__file__).parent / "dict.txt"
        freq = {}
        for line in dict_path.open(encoding="utf-8"):
            cols = line.strip().split()
            if len(cols) >= 2:
                freq[cols[0]] = int(cols[1])
        print(f"词频词典已加载：{len(freq)} 条")
        return freq
    except Exception as exc:
        print(f"警告：jieba 词频不可用（{exc}），仅做结构校验")
        return {}


def load_idioms():
    """下载并缓存成语词典，返回 {成语: 词频}。"""
    data = None
    if IDIOM_CACHE.exists() and time.time() - IDIOM_CACHE.stat().st_mtime < 7 * 86400:
        try:
            data = json.loads(IDIOM_CACHE.read_text(encoding="utf-8"))
        except Exception:
            data = None
    if data is None:
        print("下载成语词典（约 6MB，仅首次）…")
        req = urllib.request.Request(IDIOM_URL, headers={"User-Agent": "kepu-word-dict/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        IDIOM_CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return {item["word"] for item in data if isinstance(item, dict) and item.get("word")}


def valid_word(word, char, freq):
    return (
        isinstance(word, str)
        and 2 <= len(word) <= 4
        and is_hanzi_string(word)
        and char in word
        and (not freq or freq.get(word, 0) >= 30)
    )


def valid_idiom(word, char, idioms, freq):
    return (
        isinstance(word, str)
        and len(word) == 4
        and is_hanzi_string(word)
        and char in word
        and word in idioms
        and (not freq or freq.get(word, 0) >= 5)
    )


def call_api(messages, api_key, model, max_tokens=4000, timeout=90):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        "https://apihub.agnes-ai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


SYSTEM_PROMPT = """你是小学语文老师，为单个汉字生成适合 6-12 岁孩子的常用组词。
严格要求：
1. 每个字给 4 个真实存在的 2-3 字常用词，词中必须包含该字
2. 只给词语本身，不要成语、不要解释、不要拼音
3. 严禁生造词、古语、生僻词；不确定就不要输出
4. 输出严格的 JSON 数组，格式：[{"char":"水","words":["喝水","水果","雨水","海水"]}]
5. 不要 markdown 代码块，不要任何说明文字"""


def generate_words(chars, api_key, model):
    """批量请求组词，返回 {char: [words]}。"""
    prompt = SYSTEM_PROMPT + "\n\n汉字列表：" + "、".join(chars) + "\n请为列表中每个字输出一条记录。"
    raw = call_api(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        api_key,
        model,
    )
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    items = json.loads(raw)
    if not isinstance(items, list):
        raise ValueError("AI 返回格式不是数组")
    result = {}
    for item in items:
        if isinstance(item, dict) and item.get("char") in chars and isinstance(item.get("words"), list):
            result[item["char"]] = item["words"]
    return result


def save(data):
    DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "count": len(data),
        },
        "chars": data,
    }
    tmp = DICT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(DICT_PATH)


def main():
    parser = argparse.ArgumentParser(description="生成汉字组词静态词典")
    parser.add_argument("--limit", type=int, default=0, help="最多补多少个新汉字（0 表示全部）")
    parser.add_argument("--batch-size", type=int, default=40, help="每次 API 请求的汉字数")
    parser.add_argument("--workers", type=int, default=3, help="并发请求数")
    parser.add_argument("--repair-empty", action="store_true", help="重新生成组词为空的汉字")
    parser.add_argument("--force", action="store_true", help="即使已有词典也重新生成全部汉字")
    args = parser.parse_args()

    api_key = require_api_key()
    cfg = load_config()
    model = cfg.get("ai", {}).get("model", "agnes-3.0-flash")
    freq = load_word_freq()
    idioms = load_idioms()

    existing = {}
    if DICT_PATH.exists() and not args.force:
        existing = json.loads(DICT_PATH.read_text(encoding="utf-8")).get("chars", {})
    print(f"词典已有 {len(existing)} 个汉字")

    all_chars = collect_chars()
    missing = [
        c for c in all_chars
        if c not in existing or (args.repair_empty and not existing[c].get("w"))
    ]
    if args.limit:
        missing = missing[: args.limit]
    print(f"待生成 {len(missing)} 个汉字，模型 {model}")
    if not missing:
        save(existing)
        return

    def build_entry(char, words_map):
        words = []
        for w in words_map.get(char, []):
            if valid_word(w, char, freq) and w not in words:
                words.append(w)
            if len(words) >= 5:
                break
        candidates = [w for w in idioms if char in w and valid_idiom(w, char, idioms, freq)]
        candidates.sort(key=lambda w: (-freq.get(w, 0), w))
        return {"w": words, "i": candidates[:3]}

    def process_batch(batch):
        for attempt in range(1, 4):
            try:
                words_map = generate_words(batch, api_key, model)
                return {char: build_entry(char, words_map) for char in batch}, True
            except Exception as exc:
                print(f"  批次第 {attempt} 次失败：{type(exc).__name__}: {str(exc)[:160]}")
                if attempt < 3:
                    time.sleep(3 * attempt)
        # 全部失败时仍给出成语兜底，避免点击后完全空白
        return {char: build_entry(char, {}) for char in batch}, False

    from concurrent.futures import ThreadPoolExecutor, as_completed

    data = dict(existing)
    failed = 0
    batches = [missing[i : i + args.batch_size] for i in range(0, len(missing), args.batch_size)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_batch, batch): idx for idx, batch in enumerate(batches, 1)}
        done = 0
        for future in as_completed(futures):
            idx = futures[future]
            entries, ok = future.result()
            data.update(entries)
            if not ok:
                failed += 1
            done += 1
            if done % 5 == 0 or done == len(batches):
                save(data)
                print(f"  进度 {done}/{len(batches)}，已保存 {len(data)} 字")

    save(data)
    print(f"完成：{len(data)} 字，失败批次 {failed}，输出 {DICT_PATH.relative_to(ROOT)}")
    before = sum(1 for v in existing.values() if v.get("w"))
    after = sum(1 for v in data.values() if v.get("w"))
    if failed and after <= before:
        raise SystemExit("所有批次均失败，词典未更新")


if __name__ == "__main__":
    main()
