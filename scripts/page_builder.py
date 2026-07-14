#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面构建模块 - 将 JSON 内容构建为静态 HTML 页面
"""

import json
import shutil
import re
import base64
import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import markdown
from PIL import Image


class SiteBuilder:
    def __init__(self):
        self.dist_dir = Path("dist")
        self.dist_dir.mkdir(exist_ok=True)
        
        self.content_dir = Path("content")
        self.archives_dir = self.content_dir / "archives"
        
        # 设置 Jinja2 模板环境
        self.env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=False
        )
        
        # 加载配置
        with open("config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)
    
    def clean_dist(self):
        """清理构建目录"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir()
    
    def copy_assets(self):
        """复制静态资源"""
        # 图片已内嵌为 base64，无需复制
        pass

    def image_to_base64(self, image_path: str) -> str:
        """将图片压缩后转为 base64 data URL"""
        try:
            filepath = self.content_dir / "images" / image_path
            if not filepath.exists():
                return ""
            
            img = Image.open(filepath)
            
            # 转换 RGBA 为 RGB（JPEG 不支持透明通道）
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # 限制最大宽度 600px，保持比例
            max_width = 600
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
            
            # 压缩为 JPEG，质量 65
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=65, optimize=True)
            data = buffer.getvalue()
            
            b64 = base64.b64encode(data).decode("utf-8")
            return f"data:image/jpeg;base64,{b64}"
        except Exception as e:
            print(f"图片转 base64 失败: {e}")
            return ""
    
    def load_articles(self) -> list:
        """加载所有文章数据"""
        articles = []
        if not self.archives_dir.exists():
            return articles
        
        for file in sorted(self.archives_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                articles.append(data)
            except Exception as e:
                print(f"读取文章失败 {file}: {e}")
        
        return articles
    
    def build_index(self, articles: list):
        """构建首页"""
        template = self.env.get_template("index.html")
        
        # 最新文章
        latest = articles[:7] if articles else []
        
        # 给最新文章生成封面 base64
        for article in latest:
            if article.get("images"):
                article["cover_b64"] = self.image_to_base64(article["images"][0])
            else:
                article["cover_b64"] = ""
        
        # 按主题分组
        themes = {}
        for a in articles:
            tid = a.get("theme", "unknown")
            if tid not in themes:
                themes[tid] = []
            themes[tid].append(a)
        
        html = template.render(
            site=self.config["site"],
            latest=latest,
            themes=themes,
            theme_config={t["id"]: t for t in self.config["themes"]},
            config=self.config
        )
        
        (self.dist_dir / "index.html").write_text(html, encoding="utf-8")
        print("首页构建完成")
    
    def build_article_pages(self, articles: list):
        """构建文章详情页"""
        template = self.env.get_template("article.html")
        articles_dir = self.dist_dir / "article"
        articles_dir.mkdir(exist_ok=True)
        
        for article in articles:
            date_str = article.get("date", "")
            if not date_str:
                continue
            
            # 找到前后文章
            idx = next((i for i, a in enumerate(articles) if a.get("date") == date_str), -1)
            prev_article = articles[idx + 1] if idx >= 0 and idx + 1 < len(articles) else None
            next_article = articles[idx - 1] if idx > 0 else None
            
            # 渲染文章内容（Markdown -> HTML + 图片替换为 base64）
            article["content_html"] = self.render_content(
                article.get("content", ""),
                article.get("images", [])
            )
            
            html = template.render(
                site=self.config["site"],
                article=article,
                prev=prev_article,
                next=next_article,
                theme_config={t["id"]: t for t in self.config["themes"]},
                config=self.config
            )
            
            (articles_dir / f"{date_str}.html").write_text(html, encoding="utf-8")
        
        print(f"文章页构建完成，共 {len(articles)} 篇")
    
    def build_archive_pages(self, articles: list):
        """构建归档页面"""
        template = self.env.get_template("archive.html")
        
        # 按月分组
        months = {}
        for a in articles:
            month = a.get("date", "")[:7]  # YYYY-MM
            if month not in months:
                months[month] = []
            months[month].append(a)
        
        # 按主题分组
        themes = {}
        for a in articles:
            tid = a.get("theme", "unknown")
            if tid not in themes:
                themes[tid] = []
            themes[tid].append(a)
        
        html = template.render(
            site=self.config["site"],
            articles=articles,
            months=sorted(months.keys(), reverse=True),
            month_groups=months,
            themes=themes,
            theme_config={t["id"]: t for t in self.config["themes"]},
            config=self.config
        )
        
        (self.dist_dir / "archive.html").write_text(html, encoding="utf-8")
        print("归档页构建完成")
    
    def render_content(self, content: str, images: list) -> str:
        """
        将 Markdown 内容转换为 HTML，并替换图片标记为 base64
        支持多种图片标记格式：[IMAGE_1], **[IMAGE_1]**
        """
        # 清理 AI 生成的图片提示词描述
        lines = content.split('\n')
        cleaned_lines = []
        skip_blockquote = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过包含 IMAGE 标记的引用块及其后续描述行
            if stripped.startswith('>'):
                if 'IMAGE' in stripped:
                    skip_blockquote = True
                    continue
                if skip_blockquote:
                    continue

            # 遇到非引用行，停止跳过
            if skip_blockquote and not stripped.startswith('>'):
                skip_blockquote = False

            # 移除斜体图片描述行（如 *图片场景描述：...*）
            if re.match(r'^\*图片[场场描]', stripped) or re.match(r'^\*[Ii]mage\s', stripped):
                continue

            # 移除纯英文图片提示词行（以 > 开头以外的英文描述）
            if re.match(r'^[Aa] (cute|group|beautiful|young|child)', stripped) and len(stripped) > 30:
                continue

            cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines)

        # 替换图片标记为 base64 图片
        for i, img in enumerate(images):
            img_src = self.image_to_base64(img)
            if img_src:
                img_html = f'<img src="{img_src}" alt="配图" class="article-image"/>'
            else:
                img_html = ""

            pattern = re.compile(r'\*\*\[IMAGE_' + str(i+1) + r'\]\*\*|\[IMAGE_' + str(i+1) + r'\]')
            content = pattern.sub(img_html, content)

        # 清理未匹配的 IMAGE 标记
        remaining_pattern = re.compile(r'\*\*\[IMAGE_\d+\]\*\*|\[IMAGE_\d+\]')
        content = remaining_pattern.sub('', content)

        html = markdown.markdown(content, extensions=['extra'])
        return html
    
    def build(self):
        """执行完整构建"""
        print("开始构建站点...")
        self.clean_dist()
        self.copy_assets()
        
        articles = self.load_articles()
        print(f"加载了 {len(articles)} 篇文章")
        
        self.build_index(articles)
        self.build_article_pages(articles)
        self.build_archive_pages(articles)
        
        print(f"构建完成，输出目录: {self.dist_dir.absolute()}")


def main():
    builder = SiteBuilder()
    builder.build()


if __name__ == "__main__":
    main()
