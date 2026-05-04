<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="版本 2.0.0"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT 协议"/>
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="支持 Docker"/>
  <img src="https://img.shields.io/badge/k8s-native-blue.svg" alt="支持 K8s"/>
  <img src="https://img.shields.io/badge/python-3.10%2B-green.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/react-18-blue.svg" alt="React 18"/>
</p>

<h1 align="center">📚 Paper Agent 2.0</h1>
<h3 align="center">您的数字科研导师 — 企业级 AI 文献管理系统</h3>

<p align="center">
  <a href="#-核心特性">核心特性</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="docs/installation.md">安装指南</a> •
  <a href="docs/user-guide.md">用户手册</a> •
  <a href="docs/architecture.md">架构设计</a> •
  <a href="./README.md">English</a>
</p>

---

## 🎯 项目简介

Paper Agent 是一款**开源的、企业级学术研究平台**，旨在彻底改变研究人员与文献交互的方式。它超越了简单的 PDF 管理，通过**深度 AI 推理**、**语义合成**和**知识图谱分析**，帮助您：

- **发现**文献间的隐藏关联
- **分析**实验矛盾和科研空白
- **自动合成**文献综述
- **组织**AI 赋能的科研笔记本

---

## ✨ 核心特性

### 🧠 知识炼金炉

| 能力 | 说明 |
|------|------|
| **矛盾检测** | 利用多 LLM 推理自动识别论文间的冲突发现 |
| **科研空白分析** | 发现"语义真空地带"，生成高影响力研究假设 |
| **跨论文合成** | 在相关工作的方法论和结果之间建立深层联系 |
| **知识图谱** | 交互式 D3.js 可视化展示引用网络和语义关系 |

### ✍️ 写作桥梁

| 能力 | 说明 |
|------|------|
| **文献综述生成** | 自动生成 LaTeX 格式的结构化 `Related Work` 章节 |
| **公式解码** | 用通俗科学语言解释复杂数学表达式 |
| **引证问答** | AI 回答附带具体引用 `[第X页，第Y段]`，可直达原文 |

### 🔬 文档智能

| 能力 | 说明 |
|------|------|
| **智能搜索** | 关键词 + 语义向量混合搜索 |
| **AI 摘要** | 三种风格（学术版/简洁版/详细版），支持流式思考模式 |
| **论文评审** | 多维度 AI 评审（方法论、创新性、清晰度等）|
| **PDF 标注** | 浏览器内 PDF 阅读器，支持高亮和笔记 |
| **对比分析** | 2-3 篇论文的深度对比分析 |

### 🔌 集成能力

| 集成 | 说明 |
|------|------|
| **Zotero 同步** | 一键从现有 Zotero 文献库导入 |
| **arXiv 雷达** | 搜索、浏览分类、即时导入预印本 |
| **多模型支持** | OpenAI、通义千问、DeepSeek、Claude、Ollama、HuggingFace |

### 🏢 企业级能力

| 能力 | 说明 |
|------|------|
| **多租户** | 基于 JWT 认证的用户隔离与角色权限 |
| **云原生** | 支持 Kubernetes 部署、Redis 任务队列、MinIO 对象存储 |
| **水平扩展** | 多 API 副本和工作节点，支持大规模文献处理 |
| **审计日志** | 完整的 API 审计追踪 |
| **限流保护** | 内置登录 / API 限流，防御暴力攻击 |

---

## 🚀 快速开始

### Docker Compose 一键启动

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
cp .env.example .env
docker-compose up -d
```

打开 **http://localhost:3000** 注册账号即可使用。

### 本地开发模式

**后端：**
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m paper_agent.backend.main  # 启动在 :8000
```

**前端：**
```bash
cd paper_agent/frontend
npm install
npm start  # 启动在 :3000
```

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────┐
│              前端 (React)                  │
│     Material UI  |  D3.js  |  i18next     │
└──────────────────┬───────────────────────┘
                   │ HTTP / SSE 流
┌──────────────────▼───────────────────────┐
│          后端 API (FastAPI)               │
│   路由  →  服务  →  LLM 策略模式          │
└────────┬─────────┬──────────┬────────────┘
         │         │          │
    ┌────▼──┐ ┌───▼────┐ ┌───▼────────┐
    │PostgreSQL│ │ Redis  │ │  MinIO/S3  │
    │  (异步)  │ │缓存+队列│ │  对象存储   │
    └─────────┘ └────────┘ └────────────┘
         │                           │
    ┌────▼──────┐          ┌─────────▼──────┐
    │ ChromaDB  │          │  GPU 工作节点   │
    │  向量库   │          │  （可选）       │
    └───────────┘          └────────────────┘
```

详见 [架构指南](docs/architecture.md)。

---

## 🛠️ 技术栈

| 层次 | 技术 |
|------|------|
| **后端** | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) |
| **数据库** | PostgreSQL 16（生产）/ SQLite（开发）|
| **向量库** | ChromaDB + SentenceTransformer 嵌入模型 |
| **AI/LLM** | 策略模式：OpenAI, 通义千问, DeepSeek, Claude, Ollama, HuggingFace |
| **前端** | React 18, Material UI 5, D3.js, i18next |
| **缓存/队列** | Redis 7（分布式缓存 + 任务队列）|
| **对象存储** | MinIO / S3 兼容存储 |
| **基础设施** | Docker, Docker Compose, Kubernetes |

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [安装指南](docs/installation.md) | 各平台的详细安装步骤 |
| [用户手册](docs/user-guide.md) | 全功能使用说明 |
| [API 参考](docs/api.md) | 完整的 API 文档和示例 |
| [架构指南](docs/architecture.md) | 系统设计、数据流和组件 |
| [配置指南](docs/configuration.md) | 环境变量和配置项说明 |
| [部署指南](docs/deployment.md) | 生产环境部署 (Docker/K8s) |
| [贡献指南](CONTRIBUTING.md) | 如何参与贡献代码 |

---

## 🤝 参与贡献

我们欢迎各种形式的贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)：

- 🐛 报告 Bug 和功能建议
- 💻 提交代码
- 📖 完善文档
- 🌐 翻译贡献

---

## 📄 开源协议

本项目采用 **MIT 协议**。详见 [LICENSE](LICENSE)。

---

## ⭐ 支持项目

如果 Paper Agent 对您的科研有帮助，请在 GitHub 给我们一个 ⭐！

---

<p align="center"><i>为全球科研社区用心打造</i></p>
