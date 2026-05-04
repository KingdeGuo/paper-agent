# 🚀 Paper Agent 2.0: Your Digital Research Mentor

[English](./README.md) | [简体中文](./README_zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/k8s-native-blue.svg)](https://kubernetes.io/)

Paper Agent is an open-source, cluster-native academic research platform designed to transform the way researchers interact with literature. It moves beyond simple PDF management into **Knowledge Creation** through deep AI reasoning and semantic synthesis.

---

## 🌟 Key Features

### 🧠 Knowledge Distillery (炼金炉)
- **Contradiction Detection**: Automatically identifies conflicting findings across multiple papers.
- **Research Gap Analysis**: Discovers "semantic voids" and generates high-impact research hypotheses.
- **Cross-Paper Synthesis**: Connects dots between different methodologies and results.

### ✍️ Drafting Bridge (写作桥)
- **Literature Review Generator**: Automatically drafts structured `Related Work` sections in **LaTeX** format.
- **Formula Decoder**: Explains complex mathematical expressions in plain scientific language using document context.
- **Citation Grounding**: Every AI claim is backed by specific citations `[Page X, Para Y]` with direct links to the source.

### 🔌 Seamless Integration
- **Zotero Sync**: One-click import from your existing Zotero library.
- **arXiv Radar**: Track the latest pre-prints and analyze them instantly.
- **Multi-LLM Support**: Supports OpenAI, Qwen, DeepSeek, Claude, and local Ollama models.

### 🏗️ Cluster-Native Architecture
- **Distributed Processing**: Ready for Kubernetes with Redis task queues and MinIO object storage.
- **Scalability**: Handles thousands of documents across multiple worker nodes.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery.
- **Frontend**: React, Material UI, D3.js (Knowledge Graph).
- **AI**: LangChain, Vector DB (Chroma/Milvus), Multiple LLM APIs.
- **Infrastructure**: Docker, Kubernetes, MinIO.

---

## 🚀 Quick Start (Docker Compose)

```bash
git clone https://github.com/your-repo/paper-agent.git
cd paper-agent
docker-compose up -d
```
Access the UI at `http://localhost:3000`.

---

## 📖 Documentation

- [Installation Guide](./docs/installation.md)
- [Architecture Deep Dive](./docs/architecture.md)
- [API Reference](./docs/api.md)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
