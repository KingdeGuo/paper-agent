# API Reference

Complete API documentation for Paper Agent's 57 route modules.

???+ tip "Interactive API Docs"
    When the server is running, visit `/docs` (Swagger UI) or `/redoc` (ReDoc) for interactive API exploration.

## Authentication

Most endpoints require JWT authentication:

```bash
# Get token
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl http://localhost:8000/api/documents \
  -H "Authorization: Bearer <token>"
```

## API Groups

| Group | Prefix | Endpoints | Description |
|-------|--------|-----------|-------------|
| 📄 **Documents** | `/api/documents` | 8 | Upload, list, get, update, delete, download, text, chunks |
| 🔍 **Search** | `/api/search` | 6 | Simple, advanced, semantic, similar, recommendations, trending |
| 📝 **Summaries** | `/api/summary` | 6 | Generate, streaming, Q&A, get, regenerate |
| 🔬 **Review** | `/api/review` | 5 | Review, score, impact, dimensions, compare |
| 🧠 **Knowledge** | `/api/knowledge` | 5 | Document graph, global graph, visualization, stats, analyze |
| 🔗 **Citations** | `/api/citations` | 6 | Export, batch export, import BibTeX, DOI lookup, search, bibliography |
| 📖 **Reading** | `/api/reading` | 6 | Statuses, list, set status, update progress, stats, delete |
| 🤖 **Ask AI** | `/api/ask` | 2 | Ask question, streaming ask |
| 👥 **Collaboration** | `/api/collab` | 7 | Groups, comments, share, shared, activity |
| 📓 **Notebooks** | `/api/notebooks` | 4 | CRUD notebooks + entries |
| 🎯 **Discovery** | `/api/discovery` | 3 | Contradictions, gaps, threads |
| ✍️ **Drafting** | `/api/drafting` | 3 | Related work, formula decode, grounded chat |
| 🔌 **Integrations** | `/api/arxiv`, `/api/zotero` | 9 | arXiv search/import, Zotero sync |
| 📁 **Projects** | `/api/projects` | 8 | CRUD projects + papers + milestones |
| 🏷️ **Tags** | `/api/tags` | 4 | Suggest, apply, all tags, by tag |
| 📊 **Analytics** | `/api/reading-analytics` | 1 | Comprehensive reading analytics |
| 💬 **Chat** | `/api/chat` | 6 | Sessions, ask, history, update, delete |
| 🔔 **Alerts** | `/api/alerts` | 4 | Create, list, check, history |
| 🗺️ **Literature Tree** | `/api/directory` | 8 | Nodes, tree, papers, auto-classify, views, suggest |
| 👤 **Users** | `/api/users` | 7 | Register, login, profile, API keys CRUD |
| ⚙️ **System** | `/api/health`, `/api/stats`, `/api/system` | 4 | Health, stats, models, system health |

## Response Format

All endpoints return JSON:

```json
{
  "id": "uuid",
  "title": "Paper Title",
  "authors": ["Author A"],
  "year": 2024,
  ...
}
```

Errors return:

```json
{
  "detail": "Human-readable error message"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Server Error |
| 503 | Service Unavailable |

??? tip "Copy any example"
    All code blocks have a copy button in the top-right corner. Click to copy!
