# API Reference

Complete API documentation for Paper Agent. The API is available at `http://localhost:8000/api` (dev) or your configured URL.

Interactive API docs are available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## 📋 Authentication

Most endpoints require JWT authentication. Include the token in the `Authorization` header:

```http
Authorization: Bearer <your-jwt-token>
```

### Get a Token

```http
POST /api/users/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "your_username",
    "email": "user@example.com",
    "role": "user"
  }
}
```

### Register

```http
POST /api/users/register
Content-Type: application/json

{
  "username": "new_user",
  "email": "new@example.com",
  "password": "secure_password_8chars",
  "full_name": "New User"
}
```

---

## 📄 Documents

### Upload Document

```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: <pdf_file>
title: "My Paper"          (optional)
authors: "Author1, Author2"  (optional)
year: 2024                   (optional)
keywords: "AI, ML"          (optional)
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "filename": "my_paper.pdf",
  "title": "My Paper",
  "authors": ["Author1", "Author2"],
  "year": 2024,
  "status": "pending"
}
```

### List Documents

```http
GET /api/documents?skip=0&limit=100&processed=2
```

**Response:**
```json
[
  {
    "id": "uuid",
    "filename": "paper.pdf",
    "title": "Paper Title",
    "authors": ["Author A"],
    "year": 2024,
    "processed": 2,
    "upload_date": "2024-01-15T10:00:00Z"
  }
]
```

### Get Document

```http
GET /api/documents/{document_id}
```

### Update Document

```http
PUT /api/documents/{document_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "authors": ["New Author"]
}
```

### Delete Document

```http
DELETE /api/documents/{document_id}
```

### Download PDF

```http
GET /api/documents/{document_id}/download
```

### Get Document Text

```http
GET /api/documents/{document_id}/text
```

### Get Document Chunks

```http
GET /api/documents/{document_id}/chunks
```

---

## 🔍 Search

### Simple Search

```http
GET /api/search/simple?q=transformer+attention&limit=10
```

### Advanced Search

```http
GET /api/search/advanced?q=machine+learning&year=2024&author=Smith&limit=20
```

### Semantic Vector Search

```http
POST /api/search/
Content-Type: application/json

{
  "query": "deep reinforcement learning applications",
  "limit": 10,
  "threshold": 0.7
}
```

### Similar Documents

```http
GET /api/search/similar/{document_id}?limit=5
```

### Trending Documents

```http
GET /api/search/trending?limit=10
```

### Recommendations

```http
GET /api/search/recommendations?limit=5
```

---

## 📝 Summaries

### Generate Summary

```http
POST /api/summary/generate
Content-Type: application/json

{
  "document_id": "uuid",
  "max_length": 500,
  "style": "academic"
}
```

**Style options:** `academic`, `simple`, `detailed`

### Streaming Summary (SSE)

```http
POST /api/summary/generate-streaming
Content-Type: application/json

{
  "document_id": "uuid",
  "max_length": 500,
  "style": "detailed"
}
```

**Response:** Server-Sent Events stream with `<thought>` reasoning tags.

### Get Existing Summary

```http
GET /api/summary/{document_id}
```

### Regenerate Summary

```http
POST /api/summary/regenerate
Content-Type: application/json

{
  "document_id": "uuid",
  "style": "simple"
}
```

### Streaming Q&A

```http
POST /api/summary/question-streaming?document_id=uuid&question=What+is+the+main+contribution?
```

---

## 🔬 Paper Review

### AI Review

```http
POST /api/review/review/{document_id}
Content-Type: application/json

{
  "dimensions": ["methodology", "innovation", "clarity"]
}
```

**Response:**
```json
{
  "overall_score": 8.5,
  "dimensions": {
    "methodology": {"score": 9, "comment": "..."},
    "innovation": {"score": 8, "comment": "..."}
  },
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": ["...", "..."]
}
```

### Get Score

```http
GET /api/review/review/{document_id}/score
```

### Compare Papers

```http
POST /api/review/compare
Content-Type: application/json

{
  "document_ids": ["uuid1", "uuid2"],
  "aspects": ["methodology", "results"]
}
```

### Predict Impact

```http
POST /api/review/review/{document_id}/predict-impact
```

---

## 🧠 Knowledge Graph

### Get Document Graph

```http
GET /api/knowledge/graph/{document_id}?depth=2
```

### Get Global Graph

```http
GET /api/knowledge/graph/global?limit=100
```

### Get Visualization Data

```http
GET /api/knowledge/graph/visualization
```

### Get Graph Stats

```http
GET /api/knowledge/graph/stats
```

### Analyze Document Citations

```http
POST /api/knowledge/graph/analyze/{document_id}
```

---

## 🔌 Integrations

### Zotero

#### Connect Zotero
```http
POST /api/zotero/connect
Content-Type: application/json

{
  "zotero_user_id": "12345",
  "api_key": "your-zotero-api-key"
}
```

#### List Collections
```http
GET /api/zotero/collections
```

#### Import from Zotero
```http
POST /api/zotero/import/{item_key}
```

### arXiv

#### Search arXiv
```http
GET /api/arxiv/search?query=transformer&max_results=20
```

#### Get Paper
```http
GET /api/arxiv/paper/{arxiv_id}
```

#### Get Daily Papers
```http
GET /api/arxiv/daily/cs.AI?max_results=50
```

#### Import from arXiv
```http
POST /api/arxiv/import/{arxiv_id}
```

---

## 📓 Notebooks

### Create Notebook
```http
POST /api/notebooks/
Content-Type: application/json

{
  "title": "My Research Notes",
  "description": "Notes on transformer architectures"
}
```

### List Notebooks
```http
GET /api/notebooks/
```

### Add Entry
```http
POST /api/notebooks/entries
Content-Type: application/json

{
  "notebook_id": "uuid",
  "document_id": "uuid" (optional),
  "type": "insight",
  "content": "Key finding: ..."
}
```

### Get Entries
```http
GET /api/notebooks/{notebook_id}/entries
```

---

## 🎯 Discovery

### Find Contradictions
```http
POST /api/discovery/contradictions
Content-Type: application/json

{
  "doc_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Find Research Gaps
```http
POST /api/discovery/gaps
Content-Type: application/json

{
  "doc_ids": ["uuid1", "uuid2"]
}
```

### Start Research Thread
```http
POST /api/discovery/threads
Content-Type: application/json

{
  "goal": "Find methods to improve transformer efficiency",
  "doc_ids": ["uuid1", "uuid2"],
  "notebook_id": "uuid" (optional)
}
```

---

## ✍️ Drafting

### Generate Related Work
```http
POST /api/drafting/related-work
Content-Type: application/json

{
  "document_ids": ["uuid1", "uuid2", "uuid3"],
  "context": "Focus on efficiency improvements"
}
```

### Decode Formula
```http
POST /api/drafting/decode-formula
Content-Type: application/json

{
  "formula": "E = mc^2",
  "document_ids": ["uuid1"]
}
```

### Grounded Chat
```http
POST /api/drafting/grounded-chat
Content-Type: application/json

{
  "document_ids": ["uuid1"],
  "question": "What datasets were used for evaluation?"
}
```

---

## 📎 Annotations

### Get Annotations
```http
GET /api/annotations/{document_id}?page=3
```

### Create Annotation
```http
POST /api/annotations/{document_id}
Content-Type: application/json

{
  "page_number": 3,
  "text": "Important finding...",
  "position_x": 100,
  "position_y": 200,
  "width": 300,
  "height": 50,
  "highlight_color": "#FFEB3B",
  "note": "This is key for my research"
}
```

### Get Notes
```http
GET /api/annotations/{document_id}/notes
```

### Create Note
```http
POST /api/annotations/{document_id}/notes
Content-Type: application/json

{
  "page_number": 5,
  "content": "This proves the hypothesis from paper X",
  "color": "#FFF9C4",
  "tags": ["important", "methodology"]
}
```

---

## 📊 BibTeX Export

### Export Single
```http
GET /api/bibtex/export/{document_id}
```

### Export Batch
```http
POST /api/bibtex/export
Content-Type: application/json

{
  "document_ids": ["uuid1", "uuid2", "uuid3"]
}
```

---

## 💻 System

### Health Check
```http
GET /api/health
```

### System Stats
```http
GET /api/stats
```

### Supported Models
```http
GET /api/system/models
```

---

## 📝 Error Handling

All errors return a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (e.g., arXiv down) |

---

## ⚡ Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/api/users/login` | 30 req/min per IP |
| `/api/users/register` | 30 req/min per IP |
| All other `/api/` | No limit (configurable) |
