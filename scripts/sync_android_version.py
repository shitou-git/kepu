#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 config.json 的版本号同步到安卓项目的 build.gradle
"""

import json
import re
from pathlib import Path
from datetime import datetime


def main():
    # 读取 config.json
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    version_name = config.get("version", "1.0.0")

    # versionCode: 使用日期格式 YYYYMMDD + 当日序号（避免重复）
    today = datetime.now().strftime("%Y%m%d")
    # 简单用 1 作为当日序号（GitHub Actions 每次 push 版本都会变）
    version_code = int(today + "01")

    build_gradle = Path("android/app/build.gradle")
    content = build_gradle.read_text(encoding="utf-8")

    # 替换 versionCode
    content = re.sub(
        r'versionCode \d+',
        f'versionCode {version_code}',
        content
    )

    # 替换 versionName
    content = re.sub(
        r'versionName "[^"]*"',
        f'versionName "{version_name}"',
        content
    )

    build_gradle.write_text(content, encoding="utf-8")
    print(f"安卓版本已同步: versionCode={version_code}, versionName={version_name}")


if __name__ == "__main__":
    main()
