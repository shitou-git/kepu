#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 kepu.png 生成安卓应用图标
直接使用完整的 kepu.png 作为图标，包括自适应图标
"""

from PIL import Image
from pathlib import Path

SIZES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

BASE_DIR = Path("android/app/src/main/res")
SOURCE_ICON = Path("kepu.png")


def main():
    source = Image.open(SOURCE_ICON).convert("RGBA")
    
    for density, size in SIZES.items():
        mipmap_dir = BASE_DIR / f"mipmap-{density}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)
        
        icon = source.resize((size, size), Image.LANCZOS)
        icon.save(mipmap_dir / "ic_launcher.png", "PNG")
        icon.save(mipmap_dir / "ic_launcher_round.png", "PNG")
        
        adaptive_size = int(size * 1.125)
        adaptive = source.resize((adaptive_size, adaptive_size), Image.LANCZOS)
        adaptive.save(mipmap_dir / "ic_launcher_foreground.png", "PNG")
        
        print(f"生成 {density} ({size}x{size}) 图标")
    
    print("图标生成完成")


if __name__ == "__main__":
    main()
