<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version 2.0.0"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT"/>
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker Ready"/>
  <img src="https://img.shields.io/badge/k8s-native-blue.svg" alt="K8s Native"/>
  <img src="https://img.shields.io/badge/python-3.10%2B-green.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/react-18-blue.svg" alt="React 18"/>
</p>

<h1 align="center">📚 Paper Agent 2.0</h1>
<h3 align="center">Your Digital Research Mentor — AI-Powered Academic Literature Management</h3>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="docs/installation.md">Installation</a> •
  <a href="docs/user-guide.md">User Guide</a> •
  <a href="docs/api.md">API</a> •
  <a href="docs/architecture.md">Architecture</a> •
  <a href="./README_zh.md">中文</a>
</p>

---

## 🎯 What is Paper Agent?

Paper Agent is an **open-source, enterprise-grade academic research platform** that transforms how researchers interact with literature. It goes far beyond simple PDF management — using **deep AI reasoning**, **semantic synthesis**, and **knowledge graph analysis** to help you:

- **Discover** hidden connections between papers
- **Analyze** contradictions and research gaps
- **Synthesize** literature reviews automatically
- **Organize** your research with AI-powered notebooks

---

## ✨ Features

### 🧠 Knowledge Distillery
| Capability | Description |
|------------|-------------|
| **Contradiction Detection** | Automatically identifies conflicting findings across papers using multi-LLM reasoning |
| **Research Gap Analysis** | Discovers "semantic voids" and generates high-impact research hypotheses |
| **Cross-Paper Synthesis** | Connects methodologies and results across related work |
| **Knowledge Graph** | Interactive D3.js visualization of citation networks and semantic relationships |

### ✍️ Drafting Bridge
| Capability | Description |
|------------|-------------|
| **Literature Review Generator** | Drafts structured `Related Work` sections in LaTeX format |
| **Formula Decoder** | Explains complex mathematical expressions in plain language |
| **Citation-Grounded QA** | Every AI claim includes specific citations `[Page X, Para Y]` with source links |

### 🔬 Document Intelligence
| Capability | Description |
|------------|-------------|
| **Smart Search** | Hybrid keyword + semantic vector search across your library |
| **AI Summarization** | Three styles (academic/simple/detailed) with streaming thinking mode |
| **Paper Review** | Multi-dimensional AI review (methodology, innovation, clarity, etc.) |
| **PDF Annotations** | In-browser PDF viewer with highlights and notes |
| **Comparative Analysis** | Side-by-side deep comparison of 2-3 papers |

### 🔌 Integrations
| Integration | Description |
|-------------|------------|
| **Zotero Sync** | One-click import from your existing Zotero library |
| **arXiv Radar** | Search, browse categories, and import pre-prints instantly |
| **Multi-LLM** | OpenAI, Qwen, DeepSeek, Anthropic Claude, Ollama, HuggingFace |

### 🏢 Enterprise
| Capability | Description |
|------------|-------------|
| **Multi-Tenant** | User isolation with JWT authentication and role-based access |
| **Cluster Native** | Kubernetes-ready with Redis task queues and MinIO object storage |
| **Horizontal Scaling** | Multiple API replicas and worker nodes for large-scale processing |
| **Audit Logging** | Full API audit trail for enterprise compliance |
| **Rate Limiting** | Built-in protection against brute-force attacks |

---

## 🚀 Quick Start

### One-command with Docker Compose

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
cp .env.example .env        # Configure your environment
docker-compose up -d         # Start all services
```

Then open **http://localhost:3000** and create your account.

### Bare-metal (Development)

**Backend:**
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .                     # Install the package
python -m paper_agent.backend.main   # Start on :8000
```

**Frontend:**
```bash
cd paper_agent/frontend
npm install
npm start                            # Start on :3000
```

---

## 📸 Screenshots

> *Screenshots coming soon. See the [User Guide](docs/user-guide.md) for detailed walkthroughs.*

| Page | Description |
|------|-------------|
| **Dashboard** | System overview with document stats, trending papers, and system info |
| **Documents** | Upload, manage, and search your PDF library with batch operations |
| **Search** | Hybrid semantic + keyword search with arXiv integration |
| **Knowledge Graph** | Interactive D3.js visualization of paper relationships |
| **Discovery** | AI-powered contradiction detection and research gap analysis |
| **Drafting** | LaTeX literature review generation and formula decoding |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│         Material UI  |  D3.js  |  i18next            │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / Streaming SSE
┌──────────────────────▼──────────────────────────────┐
│              Backend API (FastAPI)                   │
│   Routes  →  Services  →  LLM Strategy Pattern      │
└────────┬─────────┬──────────┬───────────────────────┘
         │         │          │
    ┌────▼──┐ ┌───▼────┐ ┌───▼────────┐
    │PostgreSQL│ │ Redis  │ │  MinIO/S3  │
    │  (Async) │ │Cache+Q │ │  Storage   │
    └─────────┘ └────────┘ └────────────┘
         │                           │
    ┌────▼──────┐          ┌─────────▼────────┐
    │ ChromaDB  │          │  GPU Workers      │
    │  Vectors  │          │  (Optional)       │
    └───────────┘          └──────────────────┘
```

See the [Architecture Guide](docs/architecture.md) for a deep dive.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 16 (production) / SQLite (development) |
| **Vector DB** | ChromaDB with SentenceTransformer embeddings |
| **AI/LLM** | Strategy pattern: OpenAI, Qwen, DeepSeek, Claude, Ollama, HuggingFace |
| **Frontend** | React 18, Material UI 5, D3.js, i18next |
| **Cache/Queue** | Redis 7 (distributed caching + task queue) |
| **Storage** | MinIO / S3-compatible object storage |
| **Infrastructure** | Docker, Docker Compose, Kubernetes |

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Installation Guide](docs/installation.md) | Detailed setup for all platforms |
| [User Guide](docs/user-guide.md) | Complete walkthrough of all features |
| [API Reference](docs/api.md) | Full API documentation with examples |
| [Architecture Guide](docs/architecture.md) | System design and data flow |
| [Configuration Guide](docs/configuration.md) | All config options and environment variables |
| [Deployment Guide](docs/deployment.md) | Production deployment (Docker, K8s) |
| [Contributing Guide](CONTRIBUTING.md) | How to contribute code |

---

## 🤝 Contributing

We welcome contributions of all kinds! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- 🐛 Bug reports & feature requests
- 💻 Code contributions
- 📖 Documentation improvements
- 🌐 Translations

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## ⭐ Support

If Paper Agent helps your research, please give us a ⭐ on GitHub! It helps other researchers discover the project.

---

<p align="center"><i>Built with ❤️ for the global research community</i></p>
