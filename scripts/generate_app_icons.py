#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 kepu.png 生成安卓应用图标
"""

from PIL import Image, ImageDraw
from pathlib import Path

# 安卓图标尺寸
SIZES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

BASE_DIR = Path("android/app/src/main/res")
SOURCE_ICON = Path("kepu.png")


def resize_icon(size: int) -> Image.Image:
    """将 kepu.png 调整为指定尺寸"""
    img = Image.open(SOURCE_ICON)
    img = img.convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return img


def make_round_icon(img: Image.Image) -> Image.Image:
    """将方形图片裁剪为圆形"""
    size = img.size[0]
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result


def make_foreground(img: Image.Image) -> Image.Image:
    """
    创建自适应图标的前景
    自适应图标要求 108dp 画布，72dp 安全区域
    实际尺寸: 108 * density
    """
    size = img.size[0]
    foreground_size = int(size * 0.72)
    fg = img.resize((foreground_size, foreground_size), Image.LANCZOS)
    return fg


def main():
    for density, size in SIZES.items():
        mipmap_dir = BASE_DIR / f"mipmap-{density}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)

        # 普通方形图标
        icon = resize_icon(size)
        icon.save(mipmap_dir / "ic_launcher.png", "PNG")

        # 圆形图标
        round_icon = make_round_icon(resize_icon(size))
        round_icon.save(mipmap_dir / "ic_launcher_round.png", "PNG")

        # 自适应图标前景 (108dp = size * 1.125)
        adaptive_size = int(size * 1.125)
        foreground = make_foreground(resize_icon(adaptive_size))
        foreground.save(mipmap_dir / "ic_launcher_foreground.png", "PNG")

        print(f"生成 {density} ({size}x{size}) 图标")

    print("图标生成完成")


if __name__ == "__main__":
    main()
