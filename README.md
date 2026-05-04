<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/version-v2.0.0-2563eb?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNNCAxOWw4LTEwIDggMTAtMTAgNyAyIDUgMTAtMTAtMTAgMTAgMTAgMTAtMTAgMi01eiIvPjwvc3ZnPg=="/>
    <img src="https://img.shields.io/badge/version-v2.0.0-2563eb?style=for-the-badge" alt="Version 2.0.0" width="130"/>
  </picture>
  <img src="https://img.shields.io/github/stars/KingdeGuo/paper-agent?style=for-the-badge&color=7c3aed" alt="GitHub Stars"/>
  <img src="https://img.shields.io/github/license/KingdeGuo/paper-agent?style=for-the-badge&color=16a34a" alt="MIT License"/>
  <img src="https://img.shields.io/badge/344_API_endpoints-2563eb?style=for-the-badge" alt="344 APIs"/>
</p>

<h1 align="center">
  📚 Paper Agent
  <br/>
  <sup>AI Research Companion — From Literature to Discovery</sup>
</h1>

<p align="center">
  <b>Open-source · Self-hosted · AI-native · Team-ready</b>
</p>

<p align="center">
  <a href="#-quick-start"><b>Quick Start</b></a> •
  <a href="docs/user-guide.md"><b>User Guide</b></a> •
  <a href="docs/api/index.md"><b>API</b></a> •
  <a href="docs/architecture/index.md"><b>Architecture</b></a> •
  <a href="mcp/"><b>MCP</b></a> •
  <a href="CONTRIBUTING.md"><b>Contributing</b></a> •
  <a href="README_zh.md"><b>中文</b></a>
</p>

<br/>

> **Paper Agent transforms how researchers interact with literature.** Upload PDFs → AI reads, summarizes, connects, and writes. From a single paper to an entire research field, in minutes, not weeks.

<br/>

---

## 🎯 Why Paper Agent?

| You're a researcher | Paper Agent helps you |
|---------------------|----------------------|
| Drowning in PDFs | AI reads them → structured summaries with citations |
| Writing lit review → takes weeks | `POST /api/agents/literature-review` → draft in seconds |
| Can't find research gaps | GraphRAG traverses citation networks → finds blind spots |
| Team needs shared reading | Workspaces with annotations, goals, activity feeds |
| Need to generate code from papers | AI → Python/Julia/R implementation code |
| Want to know "who cited whom" | Citation chains forward & backward |
| Presenting at a conference | Auto-generate slides + figures from papers |

---

## ✨ Feature Atlas

<table>
<tr>
  <td width="50%" valign="top">

  ### 📖 Reading
  - **AI Summaries** — Academic/simple/detailed styles with streaming thinking
  - **PDF Viewer** — In-browser with highlights, notes, annotations
  - **Reading List** — to-read / reading / read with progress tracking
  - **Flashcards** — SM-2 spaced repetition (Anki-algorithm)
  - **Research Journal** — Daily diary with auto-populated stats

  ### 🔍 Discovery
  - **Smart Search** — Hybrid vector + keyword across library & arXiv
  - **Multi-Source Search** — arXiv + PubMed + CrossRef + local at once
  - **GraphRAG** — Graph-based retrieval through citation networks
  - **Research Chat** — Persistent multi-session AI conversations
  - **Recommendations** — Topic-based, "read next", trending

  ### 🧠 Analysis
  - **Literature Matrix** — 10-dimension cross-paper comparison table
  - **Knowledge Graph** — D3.js interactive citation visualization
  - **Research Gaps** — AI identifies contradictions & hypotheses
  - **Paper Clustering** — Auto-cluster by topic with LLM
  - **Concept Extraction** — Build concept maps across papers
  </td>
  <td width="50%" valign="top">

  ### ✍️ Writing & Publishing
  - **Related Work Generator** — Structured LaTeX sections
  - **Review Response** — Draft point-by-point reviewer responses
  - **Grant Proposal Writer** — NSF/NIH/ERC/Horizon formats
  - **Patent Idea Extractor** — Identify patentable innovations
  - **Code Generator** — Methodology → Python/Julia/R/MATLAB
  - **Figure Generator** — Publication-quality chart code
  - **Conference Tracker** — 17 venues, CFP deadlines, submissions

  ### 🤖 AI & Automation
  - **MCP Protocol** — 19 tools for any AI assistant
  - **AI Agents** — LiteratureReview + GapAnalysis + Writing agents
  - **Skills Marketplace** — 8 built-in research skills + community
  - **Proactive Monitor** — Daily briefings, deadline alerts
  - **Memory System** — Persistent SOUL.md + MEMORY.md + AGENTS.md

  ### 👥 Team & Enterprise
  - **Workspaces** — Owner/admin/member/viewer roles
  - **Shared Annotations** — Collaborative paper discussions
  - **Team Goals** — Collective reading targets with tracking
  - **Bot Integrations** — DingTalk / Feishu / Slack / WeCom

  ### 🔧 Platform
  - **344 API endpoints** — 69 modules, full OpenAPI
  - **Self-hosted** — Your data, your infrastructure
  - **Docker / K8s** — One-command deploy, cluster scaling
  - **Dark Mode** — System-aware with manual toggle
  </td>
</tr>
</table>

---

## 🚀 Quick Start

```bash
# One command — start all services
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
cp .env.example .env
docker-compose up -d

# Open http://localhost:3000 → create account → upload a paper
```

<details>
<summary><b>Or run without Docker (bare metal)</b></summary>

```bash
# Backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt beautifulsoup4
python3 -m paper_agent.backend.main  # → http://localhost:8000

# Frontend (separate terminal)
cd paper_agent/frontend
npm install
npm start  # → http://localhost:3000
```
</details>

**First steps after setup:**
1. 📄 **Upload a PDF** → Documents → Upload
2. 🤖 **Ask AI about your library** → Ask AI
3. 🔗 **Connect AI assistants** → `pip install mcp && python mcp/server.py`
4. 🧠 **Generate flashcards** → Open a paper → Flashcards tab

---

## 🏗️ Architecture at a Glance

```
                    ┌─────────────────────────┐
                    │     Frontend (React)     │
                    │  32 pages · MUI · D3.js  │
                    └───────────┬─────────────┘
                                │ HTTP / SSE
                    ┌───────────▼─────────────┐
                    │    Backend (FastAPI)     │
                    │  69 modules · 344 APIs   │
                    └───┬──────┬──────┬───────┘
                        │      │      │
              ┌─────────▼┐ ┌──▼───┐ ┌▼──────────┐
              │PostgreSQL│ │Redis │ │  MinIO/S3 │
              │ (async)  │ │Cache+Q│ │  Storage  │
              └──────────┘ └──────┘ └───────────┘
                        │              │
              ┌─────────▼┐    ┌────────▼────────┐
              │ ChromaDB │    │  LLM Strategy   │
              │ Vectors  │    │ 6 providers      │
              └──────────┘    └─────────────────┘
```

**Key design patterns:**
- **Service Registry** — DI container, lazy init, no circular imports
- **LLM Strategy** — 6 providers, graceful fallback on failure
- **MCP Server** — 19 tools, 4 prompts, stdio transport
- **Memory System** — SOUL.md + MEMORY.md + AGENTS.md

---

## 📊 By the Numbers

<table>
<tr><th></th><th></th><th></th><th></th></tr>
<tr>
  <td align="center"><b>344</b><br/><sub>API Endpoints</sub></td>
  <td align="center"><b>69</b><br/><sub>Route Modules</sub></td>
  <td align="center"><b>32</b><br/><sub>Frontend Pages</sub></td>
  <td align="center"><b>8</b><br/><sub>AI Paradigms</sub></td>
</tr>
<tr>
  <td align="center"><b>6</b><br/><sub>LLM Providers</sub></td>
  <td align="center"><b>40+</b><br/><sub>Database Tables</sub></td>
  <td align="center"><b>10</b><br/><sub>CI/CD Pipelines</sub></td>
  <td align="center"><b>6</b><br/><sub>Research Skills</sub></td>
</tr>
</table>

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 16 (prod) / SQLite (dev) |
| **Vector DB** | ChromaDB + SentenceTransformers |
| **AI/LLM** | OpenAI · Qwen · DeepSeek · Claude · Ollama · HuggingFace |
| **Frontend** | React 18 · Material UI 5 · D3.js · i18next |
| **Infrastructure** | Docker · Docker Compose · Kubernetes |
| **CI/CD** | GitHub Actions · CodeQL · GHCR · MkDocs |

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [User Guide](docs/user-guide.md) | Complete feature walkthrough |
| [Installation Guide](docs/installation.md) | Setup for all platforms |
| [API Reference](docs/api/index.md) | 344 endpoints with examples |
| [Architecture Guide](docs/architecture/index.md) | System design & data flow |
| [Configuration Guide](docs/configuration.md) | All environment variables |
| [Deployment Guide](docs/deployment.md) | Docker & Kubernetes |
| [MCP Integration](mcp/README.md) | Connect any AI assistant |
| [Research Skills](skills/) | 6 pre-built research workflows |
| [FAQs](docs/faq.md) | Frequently asked questions |
| [Changelog](docs/changelog.md) | Release history |
| [Roadmap](docs/roadmap.md) | Upcoming features |

---

## 🤝 Contributing

We welcome all contributions — code, docs, translations, feedback.

| Area | How to start |
|------|-------------|
| 🐛 **Bug report** | Open a [GitHub Issue](https://github.com/KingdeGuo/paper-agent/issues) |
| 💡 **Feature idea** | Start a [Discussion](https://github.com/KingdeGuo/paper-agent/discussions) |
| 💻 **Code** | See [CONTRIBUTING.md](CONTRIBUTING.md) |
| 📖 **Docs** | Improve anything in `docs/` |
| 🌐 **Translation** | Add or improve i18n files |

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE).

---

<p align="center">
  <b>Built by researchers, for researchers.</b>
  <br/><br/>
  <a href="https://github.com/KingdeGuo/paper-agent">
    <img src="https://img.shields.io/github/stars/KingdeGuo/paper-agent?style=social" alt="Stars"/>
  </a>
</p>
