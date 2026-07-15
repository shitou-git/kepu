#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成5篇文章的配图 - 根据文章段落内容编写图片提示词
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from image_search import ImageFinder

# 5篇文章的新图片提示词和内容修复
ARTICLES = {
    "2026-07-04": {
        "file": "content/archives/2026-07-04.json",
        "title": "蚂蚁的超能力",
        # IMAGE_1: 信息素沟通术段落 - 蚂蚁留下气味痕迹形成蚁路
        # IMAGE_2: 移到"大自然的清洁工"段落 - 蚂蚁清理落叶分解有机物
        # IMAGE_3: 地下帝国建筑师段落 - 蚂蚁地下巢穴分工合作
        "prompts": [
            "Close-up of a line of ants following a pheromone trail on the ground, carrying small food particles, sunlight filtering through leaves, nature photography style, vibrant colors, educational science illustration for children",
            "Ants cleaning up forest floor, carrying dead leaves and organic debris back to their nest, soil enrichment concept, lush green forest background, children's science illustration style, bright and educational",
            "Cross-section illustration of an underground ant colony showing tunnels and chambers, worker ants digging, soldier ants guarding, queen ant in the center, detailed educational diagram for children, colorful cartoon style"
        ],
        # 修复内容：将IMAGE_2从信息素段落移到"大自然的清洁工"段落
        "content_fix": True
    },
    "2026-07-11": {
        "file": "content/archives/2026-07-11.json",
        "title": "火箭隔热秘密",
        # IMAGE_1: 烧蚀材料段落 - 火箭再入大气层烧蚀材料蒸发
        # IMAGE_2: 防热瓦段落 - 航天器表面防热瓦像鱼鳞
        # IMAGE_3: 生活隔热段落 - 保温杯、消防服等日常隔热
        "prompts": [
            "A spacecraft capsule re-entering Earth's atmosphere with glowing red hot plasma around it, ablative heat shield material burning away to protect the capsule, dramatic sky background, educational science illustration for children, vibrant colors",
            "Close-up of a space shuttle covered with black and white thermal protection tiles arranged like fish scales, each tile visible with texture detail, space background, children's science education illustration style",
            "Side-by-side illustration showing a thermos flask with vacuum layer diagram, a firefighter in protective suit, and a refrigerator with insulation, all connected by heat insulation concept, colorful educational infographic for kids"
        ],
        "content_fix": False
    },
    "2026-07-01": {
        "file": "content/archives/2026-07-01.json",
        "title": "中国空间站",
        # IMAGE_1: 微重力段落 - 航天员在空间站漂浮、睡袋睡觉
        # IMAGE_2: 太空大餐段落 - 航天员在太空吃饭、食物飘浮
        # IMAGE_3: 健康家园段落 - 航天员在太空锻炼
        "prompts": [
            "Chinese astronauts floating inside the Tiangong space station module, one astronaut in a sleeping bag attached to the wall, microgravity environment, Earth visible through the window, children's educational illustration style, bright colors",
            "Chinese astronauts eating a meal inside the space station, food balls floating in the air, using squeeze bags and straws, Chinese food dishes visible, warm lighting, educational science illustration for children",
            "A Chinese astronaut exercising on a specialized treadmill with resistance bands inside the space station, focused expression, large window showing Earth and stars in background, dynamic pose, children's science illustration style"
        ],
        "content_fix": False
    },
    "2026-07-02": {
        "file": "content/archives/2026-07-02.json",
        "title": "中国天眼",
        # IMAGE_1: 开篇介绍FAST - 贵州大山里的巨大射电望远镜
        # IMAGE_2: 听宇宙的悄悄话 - FAST接收宇宙无线电波
        # IMAGE_3: 如何改变形状 - FAST面板变形、馈源舱
        "prompts": [
            "Aerial view of the FAST radio telescope, a massive 500-meter dish nestled in the green karst mountains of Guizhou, China, surrounded by lush vegetation, sunny day, educational science illustration for children, vibrant colors",
            "The giant FAST telescope dish receiving faint radio waves from distant stars and galaxies in space, radio wave signals visualized as colorful lines coming from the universe, educational infographic style for children, dark blue starry background",
            "Close-up of the FAST telescope's triangular panels changing shape with steel cables, the feed cabin suspended above the center of the dish, engineering precision concept, children's science illustration style, detailed and colorful"
        ],
        "content_fix": False
    },
    "2026-06-27": {
        "file": "content/archives/2026-06-27.json",
        "title": "雷达与无人机",
        # IMAGE_1: 蝙蝠的秘密段落 - 蝙蝠回声定位原理
        # IMAGE_2: 无人机的侦察段落 - 军用无人机在高空侦察
        # IMAGE_3: 未来的战场段落 - 隐形战斗机和雷达电子战
        "prompts": [
            "A cute bat flying in a dark cave emitting sound waves that bounce off rocks and insects, echolocation principle illustrated with visible sound wave rings, educational science infographic style for children, bright colors against dark cave background",
            "A military reconnaissance drone flying high above a green valley, equipped with cameras and sensors, transmitting live video feed to a ground control station, modern technology theme, child-friendly educational illustration style",
            "A modern stealth fighter jet flying alongside a radar dish on the ground, showing how stealth design deflects radar waves, electronic warfare concept, vibrant educational illustration for children, dynamic action scene"
        ],
        "content_fix": False
    }
}


def fix_ant_content(content: str) -> str:
    """修复蚂蚁文章：将IMAGE_2从信息素段落移到"大自然的清洁工"段落"""
    # 删除连续的 [IMAGE_1]\n\n[IMAGE_2]，只保留[IMAGE_1]
    content = content.replace("[IMAGE_1]\n\n[IMAGE_2]", "[IMAGE_1]")

    # 在"大自然的清洁工"段落末尾添加[IMAGE_2]
    # 找到"每一次我们在草地上看到蚂蚁搬家，其实都是在见证一场宏大的生态循环正在进行中。"
    # 在这段话后面添加IMAGE_2
    marker = "每一次我们在草地上看到蚂蚁搬家，其实都是在见证一场宏大的生态循环正在进行中。"
    if marker in content:
        content = content.replace(
            marker,
            marker + "\n\n[IMAGE_2]"
        )

    return content


def main():
    import os
    os.environ["AGENS_API_KEY"] = "sk-lr4s7E7eiQYUeC4T47xNoQciOapqAIOFPkTLgvtd8ae7y6nZ"

    finder = ImageFinder()

    for date_str, info in ARTICLES.items():
        article_path = Path(info["file"])
        print(f"\n{'='*60}")
        print(f"处理文章: {info['title']} ({date_str})")
        print(f"{'='*60}")

        # 读取文章
        article = json.loads(article_path.read_text(encoding="utf-8"))
        print(f"标题: {article['title']}")

        # 修复内容（蚂蚁文章需要调整图片位置）
        if info.get("content_fix"):
            old_content = article["content"]
            article["content"] = fix_ant_content(old_content)
            if old_content != article["content"]:
                print("已修复内容：移动IMAGE_2到'大自然的清洁工'段落")

        # 生成新图片
        prompts = info["prompts"]
        print(f"生成 {len(prompts)} 张新图片...")

        new_images = []
        for i, prompt in enumerate(prompts):
            print(f"\n  [{i+1}/{len(prompts)}] 提示词: {prompt[:60]}...")
            image_url = finder._generate_image(prompt)
            if not image_url:
                print(f"  第{i+1}张图生成失败，重试中...")
                image_url = finder._generate_image(prompt)

            if image_url:
                local_path = finder._download_image(image_url, prompt, date_str, i+1)
                if local_path:
                    filename = Path(local_path).name
                    new_images.append(filename)
                    print(f"  成功: {filename}")
                else:
                    print(f"  下载失败，跳过")
            else:
                print(f"  生成失败，跳过")

        if not new_images:
            print(f"  ⚠️ 无图片生成成功，跳过更新")
            continue

        # 更新文章数据
        article["image_prompts"] = prompts
        article["images"] = new_images

        # 保存
        article_path.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n文章已更新: {article_path}")
        print(f"新图片: {new_images}")

    print(f"\n{'='*60}")
    print("全部完成！")


if __name__ == "__main__":
    main()
