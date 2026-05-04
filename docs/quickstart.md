# 🚀 Quick Start

Get Paper Agent running in 5 minutes.

## Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
cp .env.example .env
docker-compose up -d
```

Open **http://localhost:3000** and create your account.

### What Gets Started

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React UI |
| Backend API | 8000 | FastAPI server |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache + task queue |
| MinIO | 9000 | Object storage |

## Option 2: Bare Metal (Development)

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m paper_agent.backend.main
```

### Frontend

```bash
cd paper_agent/frontend
npm install
npm start
```

## Verify Installation

```bash
curl http://localhost:8000/health
# {"status": "healthy", "version": "2.0.0"}
```

## First Steps

1. **Upload a paper** — Go to Documents → Upload
2. **Search arXiv** — Go to Search → arXiv Global tab
3. **Generate summary** — Open a paper → Generate Summary
4. **Try Ask AI** — Go to Ask AI → Ask about your library
5. **Set up MCP** — Follow [MCP Guide](mcp.md) to connect AI assistants

## Next Steps

- [Complete Installation Guide](installation.md)
- [User Guide](user-guide/index.md)
- [Configuration Reference](configuration.md)
