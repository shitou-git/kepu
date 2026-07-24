#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成安卓闪屏图
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PRIMARY_COLOR = (44, 122, 123)  # #2c7a7b
WHITE = (255, 255, 255)
LIGHT_BG = (230, 255, 250)  # #e6fffa

# 竖屏闪屏尺寸
PORTRAIT_SIZES = {
    "mdpi": (320, 480),
    "hdpi": (480, 800),
    "xhdpi": (720, 1280),
    "xxhdpi": (1080, 1920),
    "xxxhdpi": (1440, 2560),
}

BASE_DIR = Path("android/app/src/main/res")


def create_splash(width: int, height: int) -> Image.Image:
    """创建闪屏图"""
    img = Image.new("RGB", (width, height), LIGHT_BG)
    draw = ImageDraw.Draw(img)

    # 顶部装饰条
    bar_height = height // 3
    draw.rectangle([0, 0, width, bar_height], fill=PRIMARY_COLOR)

    # 文字
    font_size = int(width * 0.12)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", int(font_size * 0.35))
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", font_size)
            small_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", int(font_size * 0.35))
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

    # 主标题
    title = "少年科普杂志"
    bbox = draw.textbbox((0, 0), title, font=font)
    text_w = bbox[2] - bbox[0]
    x = (width - text_w) / 2
    y = bar_height + (height - bar_height) / 2 - font_size
    draw.text((x, y), title, font=font, fill=PRIMARY_COLOR)

    # 副标题
    subtitle = "每天一点科学知识"
    bbox2 = draw.textbbox((0, 0), subtitle, font=small_font)
    text_w2 = bbox2[2] - bbox2[0]
    x2 = (width - text_w2) / 2
    y2 = y + font_size * 1.5
    draw.text((x2, y2), subtitle, font=small_font, fill=(113, 128, 150))

    return img


def main():
    for density, (w, h) in PORTRAIT_SIZES.items():
        # 竖屏
        dir_port = BASE_DIR / f"drawable-port-{density}"
        dir_port.mkdir(parents=True, exist_ok=True)
        splash = create_splash(w, h)
        splash.save(dir_port / "splash.png", "PNG")

        # 横屏
        dir_land = BASE_DIR / f"drawable-land-{density}"
        dir_land.mkdir(parents=True, exist_ok=True)
        splash_land = create_splash(h, w)
        splash_land.save(dir_land / "splash.png", "PNG")

        print(f"生成 {density} 闪屏图 ({w}x{h})")

    print("闪屏图生成完成")


if __name__ == "__main__":
    main()
