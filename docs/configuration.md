# Configuration Guide

All configuration options for Paper Agent.

---

## 📋 Environment Variables

The system is configured via environment variables. Copy `.env.example` to `.env` and modify as needed.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPER_AGENT_SECRET_KEY` | `paper-agent-secret-key-change-in-production` | **Must change in production.** Used for JWT token signing. |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed CORS origins. |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Database Configuration

#### Development (SQLite — no config needed)

SQLite is used by default. The database file is stored at `./data/documents.db`.

#### Production (PostgreSQL via cluster settings)

All cluster database settings use the `CLUSTER__` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLUSTER__ENABLE_CLUSTERING` | `false` | Enable cluster mode |
| `CLUSTER__DATABASE__TYPE` | `sqlite` | `sqlite` or `postgresql` |
| `CLUSTER__DATABASE__HOST` | `localhost` | PostgreSQL host |
| `CLUSTER__DATABASE__PORT` | `5432` | PostgreSQL port |
| `CLUSTER__DATABASE__NAME` | `paper_agent` | Database name |
| `CLUSTER__DATABASE__USER` | `paper_agent` | Database user |
| `CLUSTER__DATABASE__PASSWORD` | (empty) | Database password |
| `CLUSTER__DATABASE__POOL_SIZE` | `10` | Connection pool size |
| `CLUSTER__DATABASE__MAX_OVERFLOW` | `20` | Max overflow connections |
| `CLUSTER__DATABASE__POOL_RECYCLE` | `3600` | Connection recycle time (s) |

### LLM Provider Settings

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_BASE_URL` | Custom OpenAI-compatible endpoint |
| `OPENAI_MODEL_NAME` | Model name (default: `gpt-4o`) |
| `QWEN_API_KEY` | Alibaba Qwen (通义千问) API key |
| `QWEN_MODEL_NAME` | Qwen model name |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `DEEPSEEK_MODEL_NAME` | DeepSeek model name |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `ANTHROPIC_MODEL_NAME` | Claude model name |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL_NAME` | Ollama model name (default: `llama3`) |

**Preferred model order:** When multiple providers are configured, the system tries them in order and falls back to the next if one fails.

### Embedding Model

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model for vector embeddings |
| `EMBEDDING_DIMENSION` | `384` | Embedding dimension (must match model) |

### Redis (Cache & Task Queue)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLUSTER__REDIS__ENABLED` | `false` | Enable Redis |
| `CLUSTER__REDIS__HOST` | `localhost` | Redis host |
| `CLUSTER__REDIS__PORT` | `6379` | Redis port |
| `CLUSTER__REDIS__DB` | `0` | Redis database number |
| `CLUSTER__REDIS__PASSWORD` | (empty) | Redis password |

### MinIO / Object Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `CLUSTER__STORAGE__ENABLED` | `false` | Enable object storage |
| `CLUSTER__STORAGE__PROVIDER` | `minio` | Storage provider: `minio`, `aws_s3`, `aliyun_oss` |
| `CLUSTER__STORAGE__ENDPOINT` | `http://localhost:9000` | S3-compatible endpoint |
| `CLUSTER__STORAGE__ACCESS_KEY` | (empty) | Access key |
| `CLUSTER__STORAGE__SECRET_KEY` | (empty) | Secret key |
| `CLUSTER__STORAGE__BUCKET` | `paper-agent` | Default bucket name |
| `CLUSTER__STORAGE__REGION` | `us-east-1` | Region (S3 only) |

### Task Queue

| Variable | Default | Description |
|----------|---------|-------------|
| `CLUSTER__TASK_QUEUE__TYPE` | `none` | Queue type: `redis`, `rabbitmq`, `none` |
| `CLUSTER__TASK_QUEUE__CONCURRENCY` | `4` | Concurrent tasks per worker |

### Vector Database

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_DB_PATH` | `./data/vector_db` | ChromaDB persistence path |

---

## 📁 File Structure

```
paper_agent/
├── data/
│   ├── documents.db          # SQLite database (dev)
│   ├── pdfs/                 # Stored PDF files
│   └── vector_db/            # ChromaDB vector store
├── logs/                     # Application logs (if configured)
└── config/                   # Config files
    └── config.yaml           # Optional YAML configuration
```

---

## 🔒 Security Configuration

### Production Checklist

1. **Change the secret key:**
   ```bash
   # Generate a secure random key
   python -c "import secrets; print(secrets.token_hex(32))"
   export PAPER_AGENT_SECRET_KEY="<generated-key>"
   ```

2. **Set CORS origins:**
   ```bash
   export CORS_ORIGINS="https://your-domain.com"
   ```

3. **Use PostgreSQL:**
   ```bash
   export CLUSTER__DATABASE__TYPE=postgresql
   export CLUSTER__DATABASE__PASSWORD="<secure-password>"
   ```

4. **Enable Redis for caching:**
   ```bash
   export CLUSTER__REDIS__ENABLED=true
   ```

5. **Configure object storage for PDFs:** (recommended for multi-node)
   ```bash
   export CLUSTER__STORAGE__ENABLED=true
   ```

---

## 🐳 Docker Configuration

In `docker-compose.yml`, environment variables are set directly. For production, use a `.env` file:

```bash
# .env
PAPER_AGENT_SECRET_KEY=your-secure-key
CLUSTER__DATABASE__PASSWORD=your-db-password
```

Docker Compose automatically loads `.env` variables when referenced as `${VARIABLE}` in the compose file.
