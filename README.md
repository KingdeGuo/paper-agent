<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version 2.0.0"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT"/>
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker Ready"/>
  <img src="https://img.shields.io/badge/k8s-native-blue.svg" alt="K8s Native"/>
  <img src="https://img.shields.io/badge/python-3.10%2B-green.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/react-18-blue.svg" alt="React 18"/>
  <img src="https://img.shields.io/badge/MCP-enabled-purple.svg" alt="MCP Enabled"/>
</p>

<h1 align="center">📚 Paper Agent 2.0</h1>
<h3 align="center">AI Research Companion — From Literature Management to Knowledge Creation</h3>
<h4 align="center"><i>AI for Science, embodied. Open-source. Enterprise-ready. Team-native.</i></h4>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="docs/installation.md">Installation</a> •
  <a href="docs/user-guide.md">User Guide</a> •
  <a href="docs/api.md">API</a> •
  <a href="docs/architecture.md">Architecture</a> •
  <a href="mcp/">MCP Integration</a> •
  <a href="skills/">Skills</a> •
  <a href="paper_agent/frontend/public/bookmarklet.html">Bookmarklet</a> •
  <a href="./README_zh.md">中文</a>
</p>

---

## 🎯 The Vision: AI Research Companion

Paper Agent is more than a literature management tool. It is an **AI Research Companion** — a concrete embodiment of **AI for Science** — that accompanies researchers through the **entire research lifecycle**.

```
Discovery → Comprehension → Synthesis → Writing → Publication → Impact
    ↑                                                        │
    └─────────────────── AI Feedback Loop ────────────────────┘
```

**For Individual Researchers:** Your personal AI research assistant that reads with you, remembers what you've learned, connects ideas across papers, helps you write with proper citations, and never forgets a reference.

**For Research Teams:** A shared workspace where PIs, postdocs, and students can collaboratively explore literature, annotate papers together, set team reading goals, and generate collective insights.

**For the Scientific Community:** An open-source platform that embodies the principles of open science — transparent, extensible, built for and by researchers.

### ✨ What Makes This Different?

| Dimension | Traditional Tools | Paper Agent |
|-----------|-----------------|-------------|
| **Scope** | PDF management | Full research lifecycle companion |
| **AI** | Basic search | Deep reasoning, synthesis, gap analysis |
| **Team** | Siloed | Workspaces, shared annotations, team goals |
| **Integration** | Desktop-only | MCP, DingTalk, Feishu, Slack, Webhook, Browser |
| **Extensibility** | Closed | Open-source, 36 API modules, MCP tools, Skills |
| **Data** | Vendor lock-in | Self-hosted, full ownership |

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

### 🤖 MCP Integration (AI-Native)
| Capability | Description |
|------------|-------------|
| **13 MCP Tools** | Search, analyze, cite, and manage papers via any MCP-compatible AI assistant (Claude, Copilot, Cursor, etc.) |
| **4 Research Prompts** | Pre-built templates for paper analysis, lit review, comparison, and idea generation |
| **Resource Access** | AI can read paper summaries, abstracts, and annotations directly |
| **Zero Configuration** | Plug-and-play with Claude Desktop, VS Code, Cursor, and Claude Code |

### 📋 AI Research Skills
| Skill | Description |
|-------|-------------|
| **Literature Review** | Generate structured related work sections with proper citations |
| **Deep Paper Analysis** | Systematic methodology/contribution/limitation analysis |
| **Research Gap Analysis** | Identify underexplored areas and generate novel hypotheses |
| **Daily Briefing** | Automated morning research digest with reading priorities |
| **Writing Assistant** | Academic writing with real-time citation support |
| **Systematic Review** | PRISMA-compliant full systematic literature review |

### 🎯 Smart Reading Goals
| Capability | Description |
|------------|-------------|
| **Reading Targets** | Set weekly/monthly paper reading goals with progress tracking |
| **Session Logging** | Track reading time, pages, and daily streaks |
| **Smart Recommendations** | AI suggests next papers based on your reading history |
| **Trend Analysis** | Spot emerging topics and keyword trends in your library |
| **Reading Statistics** | Visualize your reading habits over time |

### 🔔 Smart Alerts
| Capability | Description |
|------------|-------------|
| **Research Alerts** | Get notified when new papers match your saved search queries |
| **Frequency Control** | Daily/weekly alert schedule |
| **Alert History** | Timeline of all triggered notifications |
| **One-Click Check** | Manual or automatic alert scanning against new documents |

### 📁 Research Projects
| Capability | Description |
|------------|-------------|
| **Project Management** | Organize papers into research projects with deadlines and priority |
| **Paper Assignment** | Link papers to projects with status tracking |
| **Milestones** | Track project progress with completable milestones |
| **Deadline Management** | Set and track project deadlines |

### 📖 Concept Glossary
| Capability | Description |
|------------|-------------|
| **AI Term Extraction** | Auto-extract key terms and definitions from any paper |
| **Categorized Glossary** | Terms organized by category (methodology, technique, concept) |
| **Search & Filter** | Search across all extracted terminology |
| **Source Linking** | Every term linked back to its source paper |

### 🏷️ Smart Tagging
| Capability | Description |
|------------|-------------|
| **AI Tag Suggestions** | Automatically suggest relevant tags for any paper |
| **Global Tag Index** | Browse all tags across your library with paper counts |
| **Tag-Based Filtering** | Find all papers with a specific tag |
| **Custom Tags** | Apply and manage your own tag system |

### 🔄 Duplicate Detection
| Capability | Description |
|------------|-------------|
| **Title-Based Detection** | Smart duplicate detection using title similarity scoring |
| **One-Click Merge** | Merge duplicates, preserving annotations, notes, and relationships |
| **Auto-Clean** | Batch detect and merge all duplicates |
| **Conflict Resolution** | Keeps the version with richer metadata |

### 📦 Paper Collections
| Capability | Description |
|------------|-------------|
| **Curated Bundles** | Create themed collections of papers |
| **Public Sharing** | Share collections via unique share codes |
| **Collaborative Curation** | Build reading lists for students or collaborators |
| **Notes Per Paper** | Add context notes to each paper in a collection |

### 📊 Research Timeline
| Capability | Description |
|------------|-------------|
| **Temporal Distribution** | See paper counts by year across your library |
| **Topic Evolution** | Track how research topics have changed over time |
| **Author Timelines** | Publication timeline for any author in your library |
| **Trend Visualization** | Spot emerging and declining research areas |

### 🔬 Data Extraction
| Capability | Description |
|------------|-------------|
| **Key Findings Extraction** | Extract research question, methodology, findings, limitations |
| **Methodology Details** | Extract framework, dataset, metrics, baselines |
| **Cross-Paper Comparison** | Compare methodology or findings across multiple papers |
| **Structured Output** | Machine-readable JSON format for further analysis |

### 📧 Email Digest
| Capability | Description |
|------------|-------------|
| **Automated Digest** | Generate formatted email-ready digests of library activity |
| **Research Highlights** | AI-written paragraph on the most interesting research connections |
| **Activity Summary** | Recent actions, reading progress, and queue status |
| **Configurable Period** | Daily, weekly, or custom lookback windows |

### 👥 Team Research Workspaces
| Capability | Description |
|------------|-------------|
| **Team Spaces** | Create shared research workspaces with role-based access (owner/admin/member/viewer) |
| **Shared Library** | Collaborate on papers with granular view/annotate/edit permissions |
| **Collaborative Annotations** | Team-wide paper discussions, comments, and shared highlights |
| **Team Goals** | Set collective reading targets with progress tracking |
| **Activity Stream** | Real-time visibility into what your team is reading and discussing |
| **Labels** | Organize papers with team-defined label system |
| **Invitation System** | Invite members via email or share codes with 7-day expiry |
| **Team Digest** | Automated weekly summary of team research activity |

### 🤖 AI Research Assistant
| Capability | Description |
|------------|-------------|
| **Daily Agenda** | Personalized daily research plan with AI focus suggestions |
| **Weekly Briefing** | Executive-level weekly research briefing with key metrics |
| **Writing Feedback** | Structured AI feedback on academic writing (clarity, argument, rigor) |
| **Research Directions** | AI analysis of your library suggesting promising research directions |

### 🔄 Peer Review Module
| Capability | Description |
|------------|-------------|
| **Paper Submission** | Submit papers from your library for structured review |
| **Reviewer Management** | Invite reviewers, track assignments, manage deadlines |
| **Structured Review Forms** | 8-dimension scoring (novelty, methodology, rigor, clarity, etc.) |
| **Decision Workflow** | Track papers through draft→submitted→under_review→accepted/rejected |
| **Discussion Threads** | Post-review discussions between authors and reviewers |
| **Revision Tracking** | Version tracking for revised manuscripts |

### 🔌 Platform Integrations
| Capability | Description |
|------------|-------------|
| **DingTalk Robot** | Send research digests and alerts to DingTalk groups (钉钉机器人) |
| **Feishu/Lark Bot** | Receive notifications in Feishu groups (飞书机器人) |
| **Slack Webhook** | Post to any Slack channel |
| **WeCom Bot** | WeChat Work integration (企业微信机器人) |
| **Generic Webhook** | Custom webhooks with JSON payload |
| **Scheduled Delivery** | Automated daily briefings and weekly digests |

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
| [MCP Integration Guide](mcp/README.md) | Connect AI assistants to your research library |
| [AI Research Skills](skills/) | Reusable workflows for common research tasks |
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
