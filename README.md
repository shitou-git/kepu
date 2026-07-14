# 少年科普杂志 (Kepu Magazine)

> 专为 6-12 岁小学生打造的自动化科普杂志，每天 16:00 自动更新，涵盖航空航天、物理实验、榜样人物、自然动物等八大主题。

## 在线访问

部署后可通过 GitHub Pages 访问：
```
https://你的用户名.github.io/kepu
```

## 八大主题

| 主题 | 图标 | 更新日 | 内容方向 |
|------|------|--------|----------|
| 航空航天 | 🚀 | 周一、周四 | 宇宙探索、航天科技 |
| 物理小实验 | 🔬 | 周二、周五 | 趣味实验、科学原理 |
| 榜样人物 | ⭐ | 周三、周六 | 科学家故事、名人传记 |
| 科学创新 | 💡 | 周一、周五 | 前沿科技、创新发明 |
| 自然与动物 | 🐼 | 周二、周四 | 动植物世界、自然奥秘 |
| 中国故事 | 🇨🇳 | 周三、周六 | 中国成就、历史文化 |
| 古典文化 | 📜 | 周日 | 传统文化、古诗词 |
| 少年军事 | 🎖️ | 周日 | 国防知识、军事科普 |

## 项目架构

```
kepu/
├── .github/workflows/daily-update.yml  # 定时工作流（每日16:00）
├── scripts/
│   ├── generate.py                     # 主生成脚本
│   ├── ai_rewrite.py                   # AgensAI API 改写模块
│   ├── image_search.py                 # 图片搜索与下载
│   └── page_builder.py                 # 静态页面构建
├── templates/                          # Jinja2 HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── article.html
│   └── archive.html
├── content/                            # 生成的内容
│   ├── archives/                       # 文章 JSON 数据
│   ├── images/                         # 配图资源
│   └── index.json                      # 内容索引
├── config.json                         # 站点配置
├── requirements.txt                    # Python 依赖
└── README.md                           # 本文件
```

## 快速开始

### 1. 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com) 并登录
2. 点击右上角 **+** → **New repository**
3. 仓库名填写 `kepu`
4. 选择 **Public**（如需 GitHub Pages 免费托管）
5. 点击 **Create repository**

### 2. 配置密钥 (Secrets)

在仓库页面 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| 密钥名 | 说明 | 获取方式 |
|--------|------|----------|
| `AGENS_API_KEY` | AgensAI API 密钥 | [AgensAI 控制台](https://api.agens.ai) |
| `UNSPLASH_API_KEY` | Unsplash 图片 API（可选） | [Unsplash Developers](https://unsplash.com/developers) |

> 如果不配置 `UNSPLASH_API_KEY`，系统会自动使用备用图库。

### 3. 推送代码

```bash
# 克隆仓库到本地
git clone https://github.com/你的用户名/kepu.git
cd kepu

# 将本项目的所有文件复制到 kepu 目录下
# ...

# 提交并推送
git add .
git commit -m "init: 少年科普杂志项目初始化"
git push origin main
```

### 4. 启用 GitHub Pages

1. 仓库 → **Settings** → **Pages**
2. **Source** 选择 **GitHub Actions**
3. 工作流会自动部署静态站点

## 本地运行

### 环境要求

- Python 3.11+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 生成单篇文章

```bash
# 按日期自动匹配主题
python scripts/generate.py

# 指定主题生成
python scripts/generate.py --theme aerospace
python scripts/generate.py --theme 航空航天
```

### 批量生成测试数据

```bash
# 生成未来 7 天的内容
python scripts/generate.py --batch 7
```

### 构建静态站点

```bash
python scripts/page_builder.py
```

构建后的文件位于 `dist/` 目录，可直接用浏览器打开 `dist/index.html` 预览。

## 自动化说明

### 定时任务

GitHub Actions 已配置为每天 **北京时间 16:00**（UTC 08:00）自动执行：

1. 读取当前日期匹配主题
2. 调用 AgensAI API 生成少年版科普文章
3. 搜索并下载配图
4. 构建静态 HTML 页面
5. 部署到 GitHub Pages
6. 自动提交内容到仓库保存

### 手动触发

在仓库 → **Actions** → **Daily Science Magazine Update** → **Run workflow** 可手动运行。

## 配置说明

编辑 `config.json` 可自定义：

- **站点信息**：标题、副标题、作者
- **主题设置**：修改主题名称、更新日期、图标
- **AI 参数**：模型、温度、最大 token
- **内容参数**：文章长度、图片数量、目标年龄

### AI API 配置

```json
{
  "ai": {
    "api_base": "https://api.agens.ai/v1",
    "model": "agens-chat",
    "temperature": 0.8,
    "max_tokens": 2000
  }
}
```

如使用其他兼容 OpenAI API 格式的服务商，修改 `api_base` 和 `model` 即可。

## 文章数据格式

每篇文章保存为 `content/archives/YYYY-MM-DD.json`：

```json
{
  "theme": "aerospace",
  "theme_name": "航空航天",
  "date": "2026-07-14",
  "title": "文章标题",
  "summary": "50字导语",
  "keywords": ["关键词1", "关键词2"],
  "content": "正文内容（Markdown）",
  "fact_card": ["知识点1", "知识点2"],
  "thinking": ["思考问题1", "思考问题2"],
  "images": ["2026-07-14_abc123.jpg"],
  "image_prompts": ["图片描述1", "图片描述2"]
}
```

## 技术栈

- **自动化**：GitHub Actions (cron 定时任务)
- **内容生成**：Python + AgensAI API
- **图片获取**：Unsplash API / 备用图库
- **页面构建**：Jinja2 模板引擎
- **静态托管**：GitHub Pages
- **成本**：GitHub Actions + Pages 完全免费，AI API 按量计费

## 自定义开发

### 添加新主题

在 `config.json` 的 `themes` 数组中添加：

```json
{
  "id": "new_theme",
  "name": "新主题名称",
  "description": "主题描述",
  "icon": "🎯",
  "weekdays": [1, 3, 5]
}
```

### 修改页面样式

编辑 `templates/base.html` 中的 CSS 变量和样式即可全局生效。

### 接入其他 AI 服务

修改 `scripts/ai_rewrite.py` 中的 `_call_api` 方法，适配其他 API 格式。

## 许可证

MIT License

## 致谢

- 内容生成：[AgensAI](https://api.agens.ai)
- 图片资源：[Unsplash](https://unsplash.com)
- 托管服务：[GitHub Pages](https://pages.github.com)
