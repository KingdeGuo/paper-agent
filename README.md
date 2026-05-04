<!--
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Paper Agent — Bilingual README (zh-CN / en)                       │
  │  Maintain both language versions side-by-side for easy reading.    │
  └──────────────────────────────────────────────────────────────────────┘
-->

<div align="center">
  <img src="https://raw.githubusercontent.com/KingdeGuo/paper-agent/main/.github/logo.svg" alt="Paper Agent" width="120" />

  <h1>📄 Paper Agent</h1>

  <p><strong>AI 驱动的智能文献管理系统</strong> · <strong>AI-Powered Literature Management System</strong></p>

  <p>
    <a href="#-项目简介--introduction">简介 / Introduction</a> •
    <a href="#-核心功能--features">功能 / Features</a> •
    <a href="#-快速开始--quick-start">快速开始 / Quick Start</a> •
    <a href="#-tech-stack">技术栈 / Tech Stack</a> •
    <a href="#-architecture">架构 / Architecture</a> •
    <a href="#-开发指南--development">开发 / Development</a> •
    <a href="#-部署--deployment">部署 / Deployment</a> •
    <a href="#-roadmap">路线图 / Roadmap</a> •
    <a href="#-contributing">贡献 / Contributing</a> •
    <a href="#%EF%B8%8F-license">许可 / License</a>
  </p>

  <p>
    <img src="https://img.shields.io/github/last-commit/KingdeGuo/paper-agent" alt="Last Commit" />
    <img src="https://img.shields.io/github/license/KingdeGuo/paper-agent" alt="License" />
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python" />
    <img src="https://img.shields.io/badge/node-18%2B-green" alt="Node" />
    <img src="https://img.shields.io/badge/react-18-blue" alt="React" />
  </p>
</div>

---

<details open>
<summary><strong>🇨🇳 中文</strong></summary>

## 📖 项目简介

**Paper Agent** 是一款基于 **RAG（检索增强生成）** 技术的智能文献管理系统。它能够帮助你：

- **上传** PDF 文献并自动解析元数据
- **语义搜索** 你的论文库，快速定位相关内容
- **AI 摘要** 自动生成文献摘要（支持流式输出与思考过程可视化）
- **智能问答** 基于文献内容进行交互式问答
- **多语言** 界面支持中文 / 英文一键切换

> 💡 **适用场景**：学术研究者、研究生、科研团队、知识工作者。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📤 **PDF 上传** | 拖拽或选择上传，自动提取标题、作者、摘要等元数据 |
| 🔍 **语义搜索** | 基于向量嵌入的全文搜索，支持关键词 + 语义混合检索 |
| 📝 **AI 摘要** | 调用 LLM 生成结构化摘要，支持详细 / 简洁 / 要点三种风格 |
| 💬 **交互式问答** | 针对单篇论文进行深度问答，展示思考链过程 |
| 🧠 **思考模式** | 可视化 AI 的推理过程，提升结果的可信度与可解释性 |
| 🎨 **响应式 UI** | 基于 MUI 构建，桌面 / 平板 / 移动全适配 |
| 🌐 **国际化** | 内置中文与英文界面，可扩展至更多语言 |

---

## 🚀 快速开始

### 前置条件

- Python **3.10+**
- Node.js **18+**
- （可选）Docker & Docker Compose

### 1. 克隆仓库

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
```

### 2. 配置

```bash
# 复制示例配置文件
cp paper_agent/config/config.yaml.example paper_agent/config/config.yaml

# 编辑 config.yaml，填入你的 LLM API Key 等参数
vim paper_agent/config/config.yaml
```

### 3. 后端启动

```bash
# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
uvicorn paper_agent.backend.main:app --reload --port 8000
```

后端 API 文档：<http://localhost:8000/docs>

### 4. 前端启动

```bash
cd paper_agent/frontend
npm install
npm start
```

前端页面：<http://localhost:3000>

---

## 🛠 技术栈

| 层次 | 技术 |
|------|------|
| **前端框架** | React 18 + React Router 6 |
| **UI 组件库** | Material UI (MUI) 5 |
| **国际化** | react-i18next + i18next-browser-languagedetector |
| **后端框架** | FastAPI (Python) |
| **数据库** | SQLite + SQLAlchemy (异步) |
| **向量数据库** | ChromaDB |
| **嵌入模型** | Sentence-Transformers (all-MiniLM-L6-v2) |
| **LLM 服务** | OpenAI / Anthropic / 本地模型（可配置） |
| **PDF 解析** | PyPDF |
| **容器化** | Docker & Docker Compose (Nginx + Uvicorn) |

---

## 🏗 架构

```
┌──────────┐     ┌───────────────┐     ┌────────────────┐
│  Browser  │────▶│  React SPA    │────▶│  FastAPI API   │
│ (用户界面) │     │  (前端 3000)   │     │  (后端 8000)    │
└──────────┘     └───────────────┘     └────┬───────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
            ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
            │  SQLite DB    │       │  ChromaDB    │       │  LLM API     │
            │  (元数据)      │       │  (向量存储)    │       │  (GPT/Claude) │
            └──────────────┘       └──────────────┘       └──────────────┘
```

### 数据流

1. **上传** → PDF 解析 → 文本分块 → 生成向量嵌入 → 存入 ChromaDB
2. **搜索** → 查询文本 → 嵌入 → 向量相似度检索 → 返回 Top-K 结果
3. **摘要** → 提取全文 → 构建 Prompt → LLM 生成 → 流式返回 & 存储
4. **问答** → 检索相关段落 → 构建上下文 Prompt → LLM 推理 → 流式返回

---

## 💻 开发指南

### 项目结构

```
paper-agent/
├── pyproject.toml                 # Python 项目元数据 & 依赖
├── requirements.txt               # pip 依赖清单
├── docker-compose.yml             # Docker 编排
├── Dockerfile                     # 后端 Dockerfile
├── paper_agent/
│   ├── backend/
│   │   ├── main.py                # FastAPI 入口 & 生命周期
│   │   ├── api/routes/            # API 路由 (documents, search, summary)
│   │   ├── config/settings.py     # Pydantic Settings 配置管理
│   │   ├── models/document.py     # SQLAlchemy + Pydantic 模型
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── database.py        # 数据库操作
│   │   │   ├── pdf_processor.py   # PDF 解析
│   │   │   ├── vector_service.py  # 向量检索
│   │   │   └── llm_service.py     # LLM 调用
│   │   └── utils/                 # 工具函数
│   ├── config/
│   │   ├── config.yaml            # 运行时配置（已忽略）
│   │   └── config.yaml.example    # 配置模板
│   ├── data/                      # 运行时数据（已忽略）
│   ├── frontend/
│   │   ├── public/                # 静态资源
│   │   ├── src/
│   │   │   ├── components/        # 通用组件 (Header, ThinkingMode...)
│   │   │   ├── pages/             # 页面 (Dashboard, Documents, Search...)
│   │   │   ├── services/api.js    # API 客户端
│   │   │   └── i18n/              # 国际化配置 & 翻译文件
│   │   ├── Dockerfile             # 前端 Dockerfile
│   │   └── nginx.conf             # Nginx 配置（生产部署）
│   └── tests/                     # 单元测试
└── .gitignore
```

### 常用命令

```bash
# 后端开发
cd paper-agent
uvicorn paper_agent.backend.main:app --reload --port 8000

# 前端开发
cd paper_agent/frontend
npm start

# 运行测试
cd paper-agent
python -m pytest paper_agent/tests -v

# 代码格式化
pip install ruff
ruff check --fix paper_agent/

# 构建前端
cd paper_agent/frontend
npm run build
```

---

## 🐳 部署

### Docker Compose（推荐）

```bash
# 构建 & 启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

- 后端：<http://localhost:8000> | API 文档：<http://localhost:8000/docs>
- 前端：<http://localhost:3000>

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CONFIG_PATH` | `./config.yaml` | 配置文件路径 |
| `REACT_APP_API_URL` | `http://localhost:8000` | 后端 API 地址（前端容器用） |

---

## 🗺 路线图

- [x] **v1.0** — 基础 PDF 上传、语义搜索、AI 摘要
- [x] **v1.1** — 交互式问答、流式输出、思考模式、国际化
- [ ] **v2.0** — 多用户认证、文献库管理、引用导出
- [ ] **v2.1** — 知识图谱可视化、论文关联推荐
- [ ] **v2.2** — 本地 LLM 集成（Ollama / llama.cpp）、离线模式

---

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详细的开发流程。

贡献方式：

- 🐛 提交 [Issue](https://github.com/KingdeGuo/paper-agent/issues) 报告 Bug
- 💡 提交 [Issue](https://github.com/KingdeGuo/paper-agent/issues) 建议新功能
- 🔧 提交 Pull Request 改进代码或文档

---

## ❤️ 支持 & 联系

如果这个项目对你有帮助，欢迎给一颗 ⭐️ Star！

- GitHub Issues：<https://github.com/KingdeGuo/paper-agent/issues>
- 项目主页：<https://github.com/KingdeGuo/paper-agent>

---

## ⚖️ License

[MIT](./LICENSE) © 2024 Paper Agent Team

</details>

---

<details>
<summary><strong>🇬🇧 English</strong></summary>

## 📖 Introduction

**Paper Agent** is an intelligent literature management system powered by **RAG (Retrieval-Augmented Generation)**. It helps you:

- **Upload** PDF papers with automatic metadata extraction
- **Semantic search** across your paper library for fast content discovery
- **AI Summaries** generate structured summaries (streaming with thinking process visualization)
- **Interactive Q&A** — ask questions about your papers and get contextual answers
- **Multi-language UI** — switch between Chinese and English with one click

> 💡 **Use cases**: Academic researchers, graduate students, research teams, knowledge workers.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **PDF Upload** | Drag-and-drop upload with auto-extraction of title, authors, abstract |
| 🔍 **Semantic Search** | Vector-based full-text search with hybrid keyword + semantic matching |
| 📝 **AI Summarization** | LLM-generated summaries in detailed / concise / bullet styles |
| 💬 **Interactive Q&A** | Deep Q&A on individual papers with chain-of-thought display |
| 🧠 **Thinking Mode** | Visualize AI reasoning steps for transparency and trust |
| 🎨 **Responsive UI** | Built with MUI — works on desktop, tablet, and mobile |
| 🌐 **i18n** | Built-in Chinese & English, extensible to more languages |

---

## 🚀 Quick Start

### Prerequisites

- Python **3.10+**
- Node.js **18+**
- (Optional) Docker & Docker Compose

### 1. Clone

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
```

### 2. Configure

```bash
cp paper_agent/config/config.yaml.example paper_agent/config/config.yaml
# Edit config.yaml — set your LLM API key and other parameters
```

### 3. Start Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
uvicorn paper_agent.backend.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs>

### 4. Start Frontend

```bash
cd paper_agent/frontend
npm install
npm start
```

Frontend: <http://localhost:3000>

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + React Router 6 |
| **UI** | Material UI (MUI) 5 |
| **i18n** | react-i18next + i18next-browser-languagedetector |
| **Backend** | FastAPI (Python) |
| **Database** | SQLite + SQLAlchemy (async) |
| **Vector DB** | ChromaDB |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) |
| **LLM** | OpenAI / Anthropic / Local (configurable) |
| **PDF** | PyPDF |
| **Container** | Docker & Docker Compose (Nginx + Uvicorn) |

---

## 🏗 Architecture

```
┌──────────┐     ┌───────────────┐     ┌────────────────┐
│  Browser  │────▶│  React SPA    │────▶│  FastAPI API   │
│ (User UI) │     │  (Frontend)   │     │  (Backend)     │
└──────────┘     └───────────────┘     └────┬───────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
            ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
            │  SQLite DB    │       │  ChromaDB    │       │  LLM API     │
            │  (Metadata)   │       │  (Vectors)    │       │  (GPT/Claude) │
            └──────────────┘       └──────────────┘       └──────────────┘
```

### Data Flow

1. **Upload** → PDF parse → Text chunking → Embedding → ChromaDB
2. **Search** → Query → Embedding → Vector similarity → Top-K results
3. **Summarize** → Full text → Prompt → LLM → Stream & persist
4. **Q&A** → Retrieve relevant chunks → Context prompt → LLM → Stream

---

## 💻 Development

### Project Structure

```
paper-agent/
├── pyproject.toml                 # Python project metadata
├── requirements.txt               # pip dependencies
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Backend Dockerfile
├── paper_agent/
│   ├── backend/
│   │   ├── main.py                # FastAPI entry point
│   │   ├── api/routes/            # API routes
│   │   ├── config/settings.py     # Pydantic Settings
│   │   ├── models/document.py     # DB & API models
│   │   ├── services/
│   │   │   ├── database.py        # DB service
│   │   │   ├── pdf_processor.py   # PDF processing
│   │   │   ├── vector_service.py  # Vector search
│   │   │   └── llm_service.py     # LLM integration
│   │   └── utils/
│   ├── config/
│   │   ├── config.yaml.example    # Config template
│   ├── data/
│   ├── frontend/
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── components/        # Shared components
│   │   │   ├── pages/             # Page components
│   │   │   ├── services/api.js    # API client
│   │   │   └── i18n/              # i18n config & locales
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── tests/
└── .gitignore
```

### Common Commands

```bash
# Backend dev
uvicorn paper_agent.backend.main:app --reload --port 8000

# Frontend dev
cd paper_agent/frontend && npm start

# Run tests
python -m pytest paper_agent/tests -v

# Lint
pip install ruff
ruff check --fix paper_agent/

# Build frontend
cd paper_agent/frontend && npm run build
```

---

## 🐳 Deployment

### Docker Compose

```bash
# Build & start
docker compose up -d --build

# Logs
docker compose logs -f

# Stop
docker compose down
```

- Backend: <http://localhost:8000> | API docs: <http://localhost:8000/docs>
- Frontend: <http://localhost:3000>

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | `./config.yaml` | Config file path |
| `REACT_APP_API_URL` | `http://localhost:8000` | Backend API URL |

---

## 🗺 Roadmap

- [x] **v1.0** — PDF upload, semantic search, AI summary
- [x] **v1.1** — Interactive Q&A, streaming, thinking mode, i18n
- [ ] **v2.0** — Multi-user auth, library management, citation export
- [ ] **v2.1** — Knowledge graph visualization, paper recommendations
- [ ] **v2.2** — Local LLM (Ollama / llama.cpp), offline mode

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

How to contribute:

- 🐛 Submit [Issues](https://github.com/KingdeGuo/paper-agent/issues) for bugs
- 💡 Suggest features via [Issues](https://github.com/KingdeGuo/paper-agent/issues)
- 🔧 Open Pull Requests to improve code or docs

---

## ❤️ Support

If you find this project helpful, please give it a ⭐️ Star!

- GitHub Issues: <https://github.com/KingdeGuo/paper-agent/issues>
- Project Home: <https://github.com/KingdeGuo/paper-agent>

---

## ⚖️ License

[MIT](./LICENSE) © 2024 Paper Agent Team

</details>