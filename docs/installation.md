# Installation Guide

This guide covers setting up Paper Agent for development, production, and all environments in between.

---

## 📋 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | >= 3.10 | Backend runtime |
| Node.js | >= 18 | Frontend build & runtime |
| npm | >= 9 | Frontend package management |
| Docker | >= 24 | Containerized deployment (optional) |
| Docker Compose | >= v2 | Multi-service orchestration (optional) |

---

## 🚀 Option 1: Docker Compose (Recommended)

The fastest way to get a fully functional instance running.

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent

# Create environment config
cp .env.example .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

**Services started:**

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React UI |
| Backend API | 8000 | FastAPI server |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & task queue |
| MinIO | 9000 | Object storage |

**Access:**
- UI: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

---

## 💻 Option 2: Development (Bare Metal)

### 1. Clone & Prepare

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install the project package
pip install -e .

# Optional: install dev tools
pip install -e ".[dev]"
```

**Configure environment:**

```bash
# macOS/Linux
export PAPER_AGENT_SECRET_KEY="your-secure-random-secret"

# Or use .env file
echo "PAPER_AGENT_SECRET_KEY=your-random-key-here" >> .env
```

**Start the backend:**

```bash
python -m paper_agent.backend.main
```

The API will start at **http://localhost:8000**. Open http://localhost:8000/docs for the interactive API documentation.

### 3. Frontend Setup

```bash
cd paper_agent/frontend
npm install
```

**Start the frontend:**

```bash
npm start
```

The UI will start at **http://localhost:3000**.

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "2.0.0"}
```

---

## 🔧 Option 3: Production Deployment

See the [Deployment Guide](deployment.md) for:

- Kubernetes deployment with Helm charts
- Production Docker Compose with SSL/TLS
- Load balancing and horizontal scaling
- Backup and disaster recovery
- Monitoring and alerting setup

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: no module named 'backend'` | Run `pip install -e .` from the project root |
| Docker build fails: `requirements.txt not found` | Ensure you have `requirements.txt` in the project root |
| Database errors | Delete `data/documents.db` and restart |
| Port already in use | Change the port: `--port 8001` for backend, or use `PORT=3001 npm start` for frontend |
| CORS errors | Set `CORS_ORIGINS` env variable to your frontend URL |
| ChromaDB import errors | Install sentence-transformers: `pip install sentence-transformers` |

### Getting Help

- Open a [GitHub Issue](https://github.com/KingdeGuo/paper-agent/issues)
- Check existing issues for similar problems
- Include your OS, Python version, and error logs when reporting
