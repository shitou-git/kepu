#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一加载 API 密钥：线上读 GitHub Actions Secrets，本地读 .env。"""

import os
from pathlib import Path


def load_env() -> None:
    """从仓库根目录 .env 加载环境变量；文件不存在或未装 dotenv 时静默跳过。"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_path, override=False)


def require_api_key() -> str:
    """返回 AGENS_API_KEY，缺失时给出明确指引并以非零状态退出。"""
    load_env()
    key = os.environ.get("AGENS_API_KEY", "")
    if not key:
        raise SystemExit(
            "缺少 AGENS_API_KEY：线上请在 GitHub Actions Secrets 中配置，"
            "本地请在仓库根目录 .env 中配置（.env 已被 .gitignore 忽略）"
        )
    return key
