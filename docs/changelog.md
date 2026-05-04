# Changelog

## Version 2.0.0 (Current)

### 🚀 Major Features
- **57 API Route Modules** — Complete research platform
- **26 Frontend Pages** — Full UI coverage
- **19 MCP Tools** — AI assistant integration
- **6 Research Skills** — Pre-built workflows
- **6 LLM Providers** — OpenAI, Qwen, DeepSeek, Claude, Ollama, HuggingFace

### 📚 Document Management
- PDF upload with metadata extraction
- Full-text search + semantic vector search
- AI summaries (academic/simple/detailed styles)
- Streaming thinking mode for AI responses
- In-browser PDF viewer with highlights and notes
- BibTeX import/export with citation formatting (APA, MLA, Chicago, IEEE)

### 🧠 AI Analysis
- Contradiction detection across papers
- Research gap analysis and hypothesis generation
- Knowledge graph visualization with D3.js
- Paper review with multi-dimensional scoring
- Cross-paper comparative analysis
- Methodology critique and quality checklist

### ✍️ Writing & Publishing
- Literature review generation (LaTeX format)
- Formula decoder for mathematical expressions
- Citation management with DOI lookup
- Overleaf integration (.bib + .tex export)
- Conference deadline tracker (17 venues)
- Peer review module with structured review forms

### 👥 Team Collaboration
- Research workspaces with role-based access
- Shared document libraries with permissions
- Collaborative annotations and discussions
- Team reading goals and activity feeds
- Paper collections for curated sharing
- Reading groups / journal club scheduling

### 🔌 Integrations
- **MCP Protocol** — 19 tools for AI assistants
- **Browser Extension** — One-click import from 14+ sites
- **Browser Bookmarklet** — Save papers from any page
- **DingTalk Robot** — (钉钉) group notifications
- **Feishu/Lark Bot** — (飞书) group notifications
- **Slack Webhook** — Channel integration
- **WeCom Bot** — (企业微信) notifications
- **Zotero Sync** — One-click library import
- **arXiv API** — Search, browse, import

### 🧠 Learning & Memory
- Flashcard system with SM-2 spaced repetition
- AI-generated flashcards from papers
- Concept glossary with auto-extraction
- Research codex (personal knowledge base)
- Research journal with daily entries
- Reading analytics dashboard

### 🏗️ Infrastructure
- Docker Compose for one-command setup
- Kubernetes manifests for production
- PostgreSQL (production) / SQLite (development)
- Redis caching and task queue
- MinIO/S3 object storage
- 40+ database tables

### 🔒 Security
- JWT authentication with PBKDF2-SHA256 (600k iterations)
- Role-based access control (admin/user/viewer)
- Multi-tenant data isolation
- Rate limiting on auth endpoints
- Audit logging for API requests
- CORS configuration from environment

### 🎯 Smart Features
- Research alerts for new paper matches
- Reading goals with progress tracking
- Literature directory tree with AI classification
- Unified search across all data sources
- Data quality engine with auto-clean
- System health monitoring
- First-run onboarding wizard
- Multi-source search (arXiv + PubMed + CrossRef + local)

### 🌐 Localization
- English and Chinese (中文) UI
- i18n support throughout
- i18n key fallback system

## Version 1.1.0
- Initial open-source release
- Basic document management
- Simple search functionality
- Core API structure
