# Architecture Guide

This document describes the system architecture, component interactions, and design decisions behind Paper Agent.

---

## 📐 System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         Frontend (React SPA)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐   │
│  │ Material  │ │  D3.js   │ │ React    │ │  i18next          │   │
│  │    UI     │ │  Graph   │ │ Router   │ │  (en/zh)          │   │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘   │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP REST + SSE Streaming
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                      Backend (FastAPI)                            │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐   │
│  │  API Routes  │─▶│  Services   │─▶│   LLM Strategy Pattern │   │
│  │  (13 files)  │  │  (16 files) │  │  ┌────────────────┐   │   │
│  └─────────────┘  └─────────────┘  │  │ OpenAI │ Qwen  │   │   │
│        │                │          │  ├────────────────┤   │   │
│        ▼                ▼          │  │ DeepSeek│Claude│   │   │
│  ┌─────────────┐  ┌─────────────┐  │  ├────────────────┤   │   │
│  │  Middleware   │  │  Registry   │  │  │ Ollama │ HF   │   │   │
│  │ Auth/Audit   │  │   (DI)     │  │  └────────────────┘   │   │
│  └─────────────┘  └─────────────┘  └────────────────────────┘   │
└──────┬────────────┬──────────────┬──────────────────────────────┘
       │            │              │
       ▼            ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│PostgreSQL│ │  Redis   │ │    MinIO     │
│ (Async)  │ │Cache+Task│ │  Object      │
│          │ │  Queue   │ │  Storage     │
└──────────┘ └──────────┘ └──────────────┘
       │                          │
       ▼                          ▼
┌──────────┐              ┌──────────────┐
│ ChromaDB │              │  Workers     │
│ Vectors  │              │  (async)     │
└──────────┘              └──────────────┘
```

---

## 🧩 Component Details

### Frontend (`paper_agent/frontend/`)

| Module | Technology | Purpose |
|--------|-----------|---------|
| **Pages** (11) | React Functional Components | Route-level views (Dashboard, Documents, Search, etc.) |
| **Components** (7) | Reusable React Components | PDFViewer, KnowledgeGraph, ThinkingMode, etc. |
| **Services** (1) | Axios | API client with JWT interceptor |
| **Contexts** (2) | React Context API | Auth state, global Snackbar notifications |
| **i18n** | i18next | English (en) and Chinese (zh) translations |

**Key Design Decisions:**
- Material UI for consistent, production-quality UI components
- D3.js for interactive knowledge graph visualization
- Streaming SSE for real-time AI thinking process display
- Context-based state management (no Redux overhead for this scale)

### Backend (`paper_agent/backend/`)

| Module | Files | Purpose |
|--------|-------|---------|
| **Routes** | 13 | API endpoint definitions, grouped by domain |
| **Services** | 16 | Business logic, database access, external integrations |
| **Models** | 4 | SQLAlchemy ORM models + Pydantic schemas |
| **Middleware** | 2 | Auth validation, audit logging |
| **Config** | 2 | App settings, cluster configuration |

**Key Design Patterns:**

**Service Registry Pattern** (`services/registry.py`):
- Centralized dependency injection
- Lazy initialization of services
- Avoids circular imports between route modules and service modules

**LLM Strategy Pattern** (`services/llm_service.py`):
- Unified interface for 6 different LLM providers
- Graceful degradation (falls back through providers)
- Streaming support for real-time responses
- Provider-specific optimizations (e.g., Qwen's long context)

**Repository Pattern** (`services/cluster_database.py`):
- Async-first database operations
- Supports both SQLite (dev) and PostgreSQL (prod)
- Soft deletes for data safety
- Built-in pagination, filtering, and search

---

## 🔄 Data Flow

### Document Upload & Processing

```
User uploads PDF
       │
       ▼
FastAPI receives file
       │
       ├─▶ Save PDF to local storage OR MinIO
       ├─▶ Extract text via pdfplumber/PyPDF2
       ├─▶ Chunk text into segments
       ├─▶ Create ChromaDB embeddings
       └─▶ Enqueue background processing
                │
                ▼
          Worker processes:
          ├─▶ Generate AI summary
          ├─▶ Extract citations
          └─▶ Build knowledge graph edges
```

### Search Flow

```
User enters query
       │
       ▼
Smart Search (hybrid):
├─▶ Vector search in ChromaDB (semantic)
├─▶ Keyword search in PostgreSQL (literal)
└─▶ Merge and rank results by relevance
       │
       ▼
Return sorted results with scores
```

### Streaming AI Response

```
User requests summary/review
       │
       ▼
Backend generates response via LLM
       │
       ├─▶ Parse <thought>...</thought> tags
       ├─▶ Stream thought process first
       ├─▶ Then stream final answer
       └─▶ Client renders progressively
```

---

## 🗄️ Database Schema

### Core Tables

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `documents` | id, title, authors, year, abstract, file_path, processed, user_id, tenant_id | Document metadata |
| `users` | id, username, email, hashed_password, role, api_keys | User accounts |
| `notebooks` | id, user_id, title, description | Research notebooks |
| `notebook_entries` | id, notebook_id, document_id, type, content | Notebook entries |
| `research_threads` | id, user_id, goal, messages, context_docs | AI research sessions |
| `zotero_credentials` | id, user_id, zotero_user_id, access_token | Zotero integration |
| `annotations` | id, document_id, page_number, text, position_x/y, width, height | PDF highlights |
| `notes` | id, document_id, page_number, content, tags | PDF notes |

### Vector Database (ChromaDB)

- Collection: `documents`
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- Distance: Cosine similarity
- Index type: HNSW

---

## 🔐 Security Architecture

### Authentication Flow

```
Login Request
    │
    ▼
Validate credentials (PBKDF2-SHA256)
    │
    ▼
Generate JWT (HS256, 24h expiry)
    │
    ▼
Client stores token in localStorage
    │
    ▼
All API requests include `Authorization: Bearer <token>`
```

### Authorization

- **Role-Based Access Control**: admin, user, viewer
- **Multi-Tenant Isolation**: Documents filtered by `user_id` and `tenant_id`
- **API Key Authentication**: Alternative auth for programmatic access

### Password Security

- Hashing: PBKDF2-SHA256 with 32-byte random salt
- Iterations: 600,000 (OWASP recommended)
- Minimum length: 8 characters

---

## 🚀 Scalability

### Horizontal Scaling

```
                 ┌──────────┐
                 │  Load    │
                 │  Balancer│
                 └────┬─────┘
              ┌───────┼───────┐
              ▼       ▼       ▼
        ┌────────┐┌────────┐┌────────┐
        │API Pod ││API Pod ││API Pod │
        │  (3x)  ││  (3x)  ││  (3x)  │
        └────────┘└────────┘└────────┘
              │       │       │
              ▼       ▼       ▼
        ┌──────────────────────────┐
        │    PostgreSQL (Primary)   │
        └──────────────────────────┘
```

- API servers are stateless — scale horizontally
- Workers can be scaled independently from API
- Redis provides distributed caching and task queuing
- MinIO provides shared storage across all nodes

---

## 📊 Performance Considerations

| Operation | Expected Time | Bottleneck |
|-----------|-------------|------------|
| PDF Upload | 1-5s (sync) | File size, extraction |
| Vector Search | <500ms | Collection size |
| AI Summary (sync) | 10-30s | LLM inference |
| AI Summary (stream) | 2-5s first token | LLM inference |
| Knowledge Graph | 1-3s | Number of nodes |
| Contradiction Detection | 15-60s | Number of papers, LLM |
