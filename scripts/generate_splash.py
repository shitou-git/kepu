#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 qi.png 生成安卓闪屏图
"""

from PIL import Image
from pathlib import Path

# 闪屏尺寸（宽 x 高）
PORTRAIT_SIZES = {
    "mdpi": (320, 480),
    "hdpi": (480, 800),
    "xhdpi": (720, 1280),
    "xxhdpi": (1080, 1920),
    "xxxhdpi": (1440, 2560),
}

BASE_DIR = Path("android/app/src/main/res")
SOURCE_SPLASH = Path("qi.png")


def resize_splash(width: int, height: int) -> Image.Image:
    """将 qi.png 调整为指定尺寸（保持比例，居中裁剪）"""
    src = Image.open(SOURCE_SPLASH)
    src = src.convert("RGB")

    src_w, src_h = src.size
    src_ratio = src_w / src_h
    target_ratio = width / height

    if src_ratio > target_ratio:
        # 源更宽，按高度缩放，裁剪两侧
        new_h = height
        new_w = int(new_h * src_ratio)
        resized = src.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - width) // 2
        cropped = resized.crop((left, 0, left + width, height))
    else:
        # 源更高，按宽度缩放，裁剪上下
        new_w = width
        new_h = int(new_w / src_ratio)
        resized = src.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - height) // 2
        cropped = resized.crop((0, top, width, top + height))

    return cropped


def main():
    for density, (w, h) in PORTRAIT_SIZES.items():
        # 竖屏
        dir_port = BASE_DIR / f"drawable-port-{density}"
        dir_port.mkdir(parents=True, exist_ok=True)
        splash = resize_splash(w, h)
        splash.save(dir_port / "splash.png", "PNG")

        # 横屏
        dir_land = BASE_DIR / f"drawable-land-{density}"
        dir_land.mkdir(parents=True, exist_ok=True)
        splash_land = resize_splash(h, w)
        splash_land.save(dir_land / "splash.png", "PNG")

        print(f"生成 {density} 闪屏图 ({w}x{h})")

    # 默认 drawable 下的 splash.png（用于 mipmap-anydpi-v26 等）
    default_splash = resize_splash(1242, 2688)  # 用 xxhdpi 尺寸
    default_drawable = BASE_DIR / "drawable" / "splash.png"
    default_drawable.parent.mkdir(parents=True, exist_ok=True)
    default_splash.save(default_drawable, "PNG")
    print(f"生成默认 splash.png")

    print("闪屏图生成完成")


if __name__ == "__main__":
    main()
