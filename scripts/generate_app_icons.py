#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成安卓应用图标
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 项目主色
PRIMARY_COLOR = (44, 122, 123)  # #2c7a7b
WHITE = (255, 255, 255)

# 安卓图标尺寸
SIZES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

BASE_DIR = Path("android/app/src/main/res")


def create_icon(size: int, text: str = "科") -> Image.Image:
    """创建圆形图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 画圆形背景
    margin = size // 20
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=PRIMARY_COLOR
    )

    # 画文字
    font_size = int(size * 0.55)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", font_size)
            except:
                font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2
    y = (size - text_h) / 2 - bbox[1] / 2

    draw.text((x, y), text, font=font, fill=WHITE)

    return img


def main():
    for density, size in SIZES.items():
        # 普通图标
        mipmap_dir = BASE_DIR / f"mipmap-{density}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)

        icon = create_icon(size)
        icon.save(mipmap_dir / "ic_launcher.png", "PNG")
        icon.save(mipmap_dir / "ic_launcher_foreground.png", "PNG")

        # 圆形图标
        round_icon = create_icon(size)
        round_icon.save(mipmap_dir / "ic_launcher_round.png", "PNG")

        print(f"生成 {density} ({size}x{size}) 图标")

    print("图标生成完成")


if __name__ == "__main__":
    main()
