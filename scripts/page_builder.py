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
        # 复制图片
        img_src = self.content_dir / "images"
        img_dst = self.dist_dir / "images"
        if img_src.exists():
            if img_dst.exists():
                shutil.rmtree(img_dst)
            shutil.copytree(img_src, img_dst)
    
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
            
            # 渲染文章内容（Markdown -> HTML + 图片替换）
            article["content_html"] = self.render_content(
                article.get("content", ""),
                article.get("images", []),
                f"article/{date_str}.html"
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
        
        html = template.render(
            site=self.config["site"],
            articles=articles,
            months=sorted(months.keys(), reverse=True),
            month_groups=months,
            theme_config={t["id"]: t for t in self.config["themes"]},
            config=self.config
        )
        
        (self.dist_dir / "archive.html").write_text(html, encoding="utf-8")
        print("归档页构建完成")
    
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
    
    def render_content(self, content: str, images: list, article_path: str = "") -> str:
        """
        将 Markdown 内容转换为 HTML，并替换图片标记
        """
        # 处理图片标记 [IMAGE_1], [IMAGE_2], [IMAGE_3]
        for i, img in enumerate(images):
            marker = f"[IMAGE_{i+1}]"
            if marker in content:
                # 计算图片相对路径
                if article_path.startswith("article/"):
                    img_src = f"../images/{img}"
                else:
                    img_src = f"images/{img}"
                img_html = f'<img src="{img_src}" alt="配图" class="article-image"/>'
                content = content.replace(marker, img_html)
        
        # 将 Markdown 转换为 HTML
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
