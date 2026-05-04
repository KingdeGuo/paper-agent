# 🚀 Paper Agent 2.0: 您的数字科研导师

[English](./README.md) | [简体中文](./README_zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/k8s-native-blue.svg)](https://kubernetes.io/)

Paper Agent 是一个开源的、云原生学术研究平台，旨在彻底改变研究人员与文献互动的方式。它超越了简单的 PDF 管理，通过深度 AI 推理和语义合成，实现从“阅读”到“**知识创造**”的跨越。

---

## 🌟 核心特性

### 🧠 知识炼金炉 (Knowledge Distillery)
- **冲突检测**: 自动识别多篇论文之间的实验结果或观点冲突。
- **科研空白分析**: 发现“语义真空地带”，生成高影响力的研究假设。
- **跨论文合成**: 在不同方法论和结果之间建立深层联系。

### ✍️ 写作桥梁 (Drafting Bridge)
- **文献综述生成器**: 自动生成符合 **LaTeX** 格式的结构化 `Related Work` 章节。
- **公式解码器**: 结合文档上下文，用通俗的科学语言解释复杂的数学表达式。
- **证据追溯**: AI 的每一句论断都带有具体的引用 `[Page X, Para Y]`，支持点击直达原文。

### 🔌 无缝集成
- **Zotero 同步**: 一键导入您现有的 Zotero 文献库。
- **arXiv 雷达**: 追踪最新的预印本并进行即时分析。
- **多模型支持**: 支持 OpenAI, 通义千问, DeepSeek, Claude 以及本地 Ollama 模型。

### 🏗️ 云原生架构
- **分布式处理**: 支持 Kubernetes 部署，集成 Redis 任务队列和 MinIO 对象存储。
- **高扩展性**: 支持在多个工作节点上处理数以万计的文献。

---

## 🛠️ 技术栈

- **后端**: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery.
- **前端**: React, Material UI, D3.js (知识图谱).
- **AI**: LangChain, 向量数据库 (Chroma/Milvus), 多 LLM API 集成.
- **基础设施**: Docker, Kubernetes, MinIO.

---

## 🚀 快速启动 (Docker Compose)

```bash
git clone https://github.com/your-repo/paper-agent.git
cd paper-agent
docker-compose up -d
```
访问 `http://localhost:3000` 即可开始使用。

---

## 🤝 参与贡献

我们欢迎任何形式的贡献！请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详细指南。

## 📄 开源协议

本项目采用 MIT 协议。详见 `LICENSE` 文件。
