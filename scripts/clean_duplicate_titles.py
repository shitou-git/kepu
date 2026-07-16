#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re

def clean_duplicate_titles(content):
    pattern = r"(###\s+.+)\n+\1"
    cleaned = re.sub(pattern, r"\1", content)
    return cleaned

def process_archives():
    archives_dir = "content/archives"
    for filename in os.listdir(archives_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(archives_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                article = json.load(f)
            
            original_content = article["content"]
            cleaned_content = clean_duplicate_titles(original_content)
            
            if original_content != cleaned_content:
                article["content"] = cleaned_content
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(article, f, ensure_ascii=False, indent=2)
                print(f"Cleaned: {filename}")
            else:
                print(f"No duplicates: {filename}")

if __name__ == "__main__":
    process_archives()
    print("\nDone!")