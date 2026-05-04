# Paper Agent — Backend Dockerfile
FROM python:3.14-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt beautifulsoup4

FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV PYTHONPATH=/app/paper_agent
RUN mkdir -p /app/paper_agent/data/pdfs /app/paper_agent/data/vector_db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "-c", "import sys; sys.path.insert(0, '/app'); sys.path.insert(0, '/app/paper_agent'); from backend.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"]
