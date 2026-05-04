# Architecture

System design overview of Paper Agent.

## High-Level Architecture

```mermaid
graph LR
    subgraph "Frontend"
        React[React SPA<br/>26 Pages]
        MUI[Material UI]
        D3[D3.js Graphs]
    end
    subgraph "Backend"
        FAST[FastAPI<br/>57 Route Modules]
        LLM[LLM Strategy<br/>6 Providers]
        MCP[MCP Server<br/>19 Tools]
    end
    subgraph "Data"
        PG[(PostgreSQL<br/>40+ Tables)]
        CH[(ChromaDB<br/>Vector Store)]
        MI[(MinIO/S3<br/>PDF Storage)]
    end
    subgraph "Infra"
        RD[Redis<br/>Cache + Queue]
        DK[Docker Compose]
        K8[Kubernetes]
    end

    React -->|HTTP/SSE| FAST
    FAST --> PG
    FAST --> CH
    FAST --> MI
    FAST --> RD
    FAST --> LLM
    MCP -->|stdio| AI[Claude/Copilot]
    AI -->|natural language| React
```

## Key Design Decisions

### Monorepo Structure
Single repository containing both frontend and backend for easier development and deployment.

### Service Registry Pattern
`backend/services/registry.py` provides centralized dependency injection, avoiding circular imports and enabling lazy initialization.

### LLM Strategy Pattern
Unified interface for 6 providers with graceful degradation — if one fails, the next is tried automatically.

### REST + SSE
Synchronous endpoints for CRUD operations, Server-Sent Events for streaming AI responses.

## By the Numbers

| Metric | Value |
|--------|-------|
| API Routes | 57 |
| Frontend Pages | 26 |
| Database Tables | 40+ |
| MCP Tools | 19 |
| LLM Providers | 6 |
| Research Skills | 6 |
| Supported Langs | 2 (EN/ZH) |
| Python Version | 3.10+ |
| React Version | 18 |
