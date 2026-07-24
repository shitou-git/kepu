#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面构建模块 - 将 JSON 内容构建为静态 HTML 页面
"""

import json
import shutil
import re
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

    def bump_version(self):
        """递增版本号并写回 config.json，用于避免浏览器加载旧缓存"""
        try:
            version = self.config.get("version", "1.0.0")
            parts = version.split(".")
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                new_version = ".".join(parts)
            else:
                new_version = "1.0.1"
            self.config["version"] = new_version

            # 写回 config.json
            self.config_path = Path("config.json")
            self.config_path.write_text(
                json.dumps(self.config, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"版本号更新: {version} -> {new_version}")
            return new_version
        except Exception as e:
            print(f"版本号更新失败: {e}")
            return self.config.get("version", "1.0.0")

    def clean_dist(self):
        """清理构建目录"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir()
    
    def copy_assets(self):
        """复制并压缩图片到 dist/images/，独立文件可走浏览器缓存"""
        img_src_dir = self.content_dir / "images"
        self.img_dst_dir = self.dist_dir / "images"
        self.img_dst_dir.mkdir(parents=True, exist_ok=True)

        if not img_src_dir.exists():
            return

        for img_file in img_src_dir.glob("*.jpg"):
            dst = self.img_dst_dir / img_file.name
            self._compress_image(img_file, dst)

    def _compress_image(self, src: Path, dst: Path):
        """压缩图片并保存为 JPEG"""
        try:
            img = Image.open(src)

            # 转换 RGBA 为 RGB（JPEG 不支持透明通道）
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 限制最大宽度 440px，保持比例
            max_width = 440
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            # 压缩为 JPEG，质量 45
            img.save(dst, format="JPEG", quality=45, optimize=True)
        except Exception as e:
            print(f"图片压缩失败 {src}: {e}")
            # 失败时直接复制原文件，保证图片不缺失
            try:
                shutil.copy(src, dst)
            except Exception:
                pass

    def image_to_url(self, image_path: str, prefix: str = "images/") -> str:
        """返回图片的相对 URL（图片已由 copy_assets 压缩到 dist/images/）"""
        if not image_path:
            return ""
        filename = Path(image_path).name
        return f"{prefix}{filename}"
    
    def load_articles(self) -> list:
        """加载所有文章数据"""
        articles = []
        if not self.archives_dir.exists():
            return articles
        
        for file in sorted(self.archives_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                # 记录文件名（不含扩展名），用于生成文章URL
                data["file_id"] = file.stem
                articles.append(data)
            except Exception as e:
                print(f"读取文章失败 {file}: {e}")
        
        return articles
    
    def build_index(self, articles: list):
        """构建首页"""
        template = self.env.get_template("index.html")
        
        # 最新文章
        latest = articles[:7] if articles else []
        
        # 给最新文章生成封面图 URL
        for article in latest:
            if article.get("images"):
                article["cover_url"] = self.image_to_url(article["images"][0], "images/")
            else:
                article["cover_url"] = ""
        
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
            file_id = article.get("file_id", "")
            date_str = article.get("date", "")
            if not file_id:
                continue
            
            # 找到前后文章
            idx = next((i for i, a in enumerate(articles) if a.get("file_id", "") == file_id), -1)
            prev_article = articles[idx + 1] if idx >= 0 and idx + 1 < len(articles) else None
            next_article = articles[idx - 1] if idx > 0 else None
            
            # 渲染文章内容（Markdown -> HTML + 图片替换为相对路径）
            article["content_html"] = self.render_content(
                article.get("content", ""),
                article.get("images", []),
                img_prefix="../images/"
            )
            
            html = template.render(
                site=self.config["site"],
                article=article,
                prev=prev_article,
                next=next_article,
                theme_config={t["id"]: t for t in self.config["themes"]},
                config=self.config
            )
            
            (articles_dir / f"{file_id}.html").write_text(html, encoding="utf-8")
        
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
    
    def render_content(self, content: str, images: list, img_prefix: str = "../images/") -> str:
        """
        将 Markdown 内容转换为 HTML，并替换图片标记为图片 URL
        图片标记 [IMAGE_N] 会被替换到对应段落末尾
        """
        # 清理 AI 生成的图片提示词描述
        lines = content.split('\n')
        cleaned_lines = []
        skip_blockquote = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过引用块中包含图片提示词的行
            if stripped.startswith('>'):
                is_prompt = False
                if any(kw in stripped for kw in ['IMAGE_PROMPTS', 'IMAGE:', 'image_prompt']):
                    is_prompt = True
                # 英文图片提示词特征词
                if any(kw in stripped.lower() for kw in ['illustration', 'cartoon style', 'children\'s book', 'educational diagram', 'vector style']):
                    is_prompt = True
                if is_prompt:
                    skip_blockquote = True
                    continue
                if skip_blockquote:
                    continue
            else:
                # 遇到非引用行，停止跳过
                skip_blockquote = False

            # 移除斜体图片描述行（如 *图片场景描述：...*）
            if re.match(r'^\*图片[场场描]', stripped) or re.match(r'^\*[Ii]mage\s', stripped):
                continue

            # 移除纯英文图片提示词行
            if re.match(r'^[Aa] (cute|group|beautiful|young|child|colorful)', stripped) and len(stripped) > 30:
                continue

            cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines)

        # 图片标记去重（每个编号只保留第一个）
        seen_markers = set()
        def dedup_marker(match):
            num = match.group(1)
            if num in seen_markers:
                return ''
            seen_markers.add(num)
            return match.group(0)
        
        content = re.sub(r'\[IMAGE_(\d+)\]', dedup_marker, content)

        # 先将 [IMAGE_N] 替换为临时占位符（使用不会被Markdown解析的格式）
        placeholders = {}
        for i, img in enumerate(images):
            img_src = self.image_to_url(img, img_prefix)
            if img_src:
                img_html = f'<img src="{img_src}" alt="配图" class="article-image" loading="lazy"/>'
            else:
                img_html = ""

            # 使用特殊字符作为占位符，避免被Markdown解析
            placeholder = f'IMAGEDOMMARKER{i+1}X'
            placeholders[placeholder] = img_html

            pattern = re.compile(r'\*\*\[IMAGE_' + str(i+1) + r'\]\*\*|\[IMAGE_' + str(i+1) + r'\]')
            content = pattern.sub(placeholder, content)

        # 清理未匹配的 IMAGE 标记
        remaining_pattern = re.compile(r'\*\*\[IMAGE_\d+\]\*\*|\[IMAGE_\d+\]')
        content = remaining_pattern.sub('', content)

        # Markdown 转 HTML
        html = markdown.markdown(content, extensions=['extra'])

        # 替换占位符为实际图片
        for placeholder, img_html in placeholders.items():
            html = html.replace(f'<p>{placeholder}</p>', img_html)  # 独占一段
            html = html.replace(placeholder, img_html)  # 在段落内

        return html
    
    def build(self):
        """执行完整构建"""
        print("开始构建站点...")
        self.bump_version()
        self.clean_dist()
        self.copy_assets()
        
        articles = self.load_articles()
        print(f"加载了 {len(articles)} 篇文章")
        
        self.build_index(articles)
        self.build_article_pages(articles)
        self.build_archive_pages(articles)
        
        self.copy_update_script()
        
        print(f"构建完成，输出目录: {self.dist_dir.absolute()}")

    def copy_update_script(self):
        """复制更新检测脚本到 dist 目录"""
        update_script = Path("templates") / "update-check.js"
        if update_script.exists():
            shutil.copy(update_script, self.dist_dir / "update-check.js")
            print("更新检测脚本已复制")


def main():
    builder = SiteBuilder()
    builder.build()


if __name__ == "__main__":
    main()
