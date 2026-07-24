#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 kepu.png 生成安卓应用图标
"""

from PIL import Image, ImageDraw
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


def extract_foreground(img: Image.Image) -> Image.Image:
    """
    从 kepu.png 中提取图标前景（去除圆形背景）
    kepu.png 是圆形图标，中心是书本+原子图案，周围是深蓝色背景
    我们需要提取中心内容，去掉边缘的圆形背景
    """
    size = img.size[0]
    img = img.convert("RGBA")
    
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)
    
    inverted_mask = Image.new("L", (size, size), 255)
    draw2 = ImageDraw.Draw(inverted_mask)
    inner_radius = int(size * 0.75)
    draw2.ellipse([(size-inner_radius)/2, (size-inner_radius)/2, 
                   (size+inner_radius)/2, (size+inner_radius)/2], fill=0)
    
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), inverted_mask)
    
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)
    
    return result


def make_adaptive_foreground(foreground_img: Image.Image, target_size: int) -> Image.Image:
    """
    创建自适应图标前景
    自适应图标画布是 108dp，安全区域是 72dp（中心区域）
    前景图片应该只包含中心的图标内容
    """
    canvas_size = target_size
    safe_size = int(target_size * 0.72)
    
    fg_scaled = foreground_img.resize((safe_size, safe_size), Image.LANCZOS)
    
    result = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset = (canvas_size - safe_size) // 2
    result.paste(fg_scaled, (offset, offset))
    
    return result


def make_background_color(color):
    """创建纯色背景"""
    colors_dir = BASE_DIR / "values"
    colors_dir.mkdir(parents=True, exist_ok=True)
    colors_content = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">{color}</color>
</resources>
"""
    with open(colors_dir / "colors.xml", "w") as f:
        f.write(colors_content)


def main():
    source = Image.open(SOURCE_ICON).convert("RGBA")
    foreground_only = extract_foreground(source)
    
    make_background_color("#2c7a7b")
    
    for density, size in SIZES.items():
        mipmap_dir = BASE_DIR / f"mipmap-{density}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)
        
        icon = source.resize((size, size), Image.LANCZOS)
        icon.save(mipmap_dir / "ic_launcher.png", "PNG")
        
        round_icon = icon.copy()
        round_icon.save(mipmap_dir / "ic_launcher_round.png", "PNG")
        
        adaptive_size = int(size * 1.125)
        adaptive_fg = make_adaptive_foreground(foreground_only, adaptive_size)
        adaptive_fg.save(mipmap_dir / "ic_launcher_foreground.png", "PNG")
        
        print(f"生成 {density} ({size}x{size}) 图标")
    
    print("图标生成完成")


if __name__ == "__main__":
    main()
