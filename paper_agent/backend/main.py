"""
Paper Agent - 企业级文献管理系统
完整后端实现
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import time

from backend.middleware.audit import AuditMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for infrastructure initialization."""
    logger.info("Starting Paper Agent...")
    try:
        from paper_agent.backend.services.registry import get_cache, get_object_storage, get_task_queue
        cache = get_cache()
        if cache:
            try:
                await cache.init()
                logger.info("Cache service initialized")
            except Exception as e:
                logger.warning(f"Cache service unavailable: {e}")

        storage = get_object_storage()
        if storage:
            try:
                await storage.init()
                logger.info("Object storage initialized")
            except Exception as e:
                logger.warning(f"Object storage unavailable: {e}")

        task_q = get_task_queue()
        if task_q:
            try:
                await task_q.init()
                logger.info("Task queue initialized")
            except Exception as e:
                logger.warning(f"Task queue unavailable: {e}")
    except Exception as e:
        logger.warning(f"Infrastructure init partial: {e}")

    try:
        from paper_agent.backend.services.registry import get_db
        db = get_db()
        if db:
            db.create_tables()
            logger.info("Database tables verified")
    except Exception as e:
        logger.warning(f"DB init skipped: {e}")

    yield
    logger.info("Shutting down Paper Agent...")


# 创建FastAPI应用
app = FastAPI(
    title="Paper Agent",
    description="企业级AI文献管理系统 - 支持集群部署",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiting middleware
rate_limit_store = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    if path.startswith("/api/users/login") or path.startswith("/api/users/register"):
        now = time.time()
        key = f"{client_ip}:{path}"
        window = rate_limit_store.get(key, [])
        window = [t for t in window if now - t < 60]
        if len(window) >= 30:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        window.append(now)
        rate_limit_store[key] = window

    response = await call_next(request)
    return response

# CORS配置
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit logging
app.add_middleware(AuditMiddleware)

# 导入并注册路由
try:
    from paper_agent.backend.api.routes import (
        documents, search, summary, users, knowledge, 
        review, arxiv, notebooks, discovery, zotero, drafting, annotations, bibtex
    )
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])
    app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge-graph"])
    app.include_router(review.router, prefix="/api/review", tags=["paper-review"])
    app.include_router(arxiv.router, prefix="/api/arxiv", tags=["arxiv"])
    app.include_router(notebooks.router, prefix="/api/notebooks", tags=["notebooks"])
    app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
    app.include_router(zotero.router, prefix="/api/zotero", tags=["zotero"])
    app.include_router(drafting.router, prefix="/api/drafting", tags=["drafting"])
    app.include_router(annotations.router, prefix="/api/annotations", tags=["annotations"])
    app.include_router(bibtex.router, prefix="/api/bibtex", tags=["bibtex"])
    logger.info("✓ 所有路由已加载（含Research Mentor + Annotations + BibTeX）")
except Exception as e:
    logger.warning(f"部分路由加载失败: {e}")

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# 系统统计
@app.get("/api/stats")
async def system_stats():
    from paper_agent.backend.services.registry import get_db, get_vector_service
    db = get_db()
    vector = get_vector_service()
    try:
        db_stats = await db.get_processing_stats() if db else {}
        vec_stats = vector.get_collection_stats() if vector else {}
        return {
            "documents": db_stats,
            "vector_db": vec_stats,
            "version": "2.0.0",
        }
    except Exception as e:
        return {"error": str(e)}

# 支持模型列表
@app.get("/api/system/models")
async def get_supported_models():
    return {
        "models": [
            {"id": "openai", "name": "OpenAI GPT"},
            {"id": "qwen", "name": "Qwen (通义千问)"},
            {"id": "deepseek", "name": "DeepSeek"},
            {"id": "ollama", "name": "Ollama"},
            {"id": "anthropic", "name": "Anthropic Claude"},
            {"id": "huggingface", "name": "HuggingFace Transformers"},
        ]
    }

# 根路径
@app.get("/")
async def root():
    return {
        "name": "Paper Agent API",
        "version": "2.0.0",
        "cluster_enabled": True,
        "features": [
            "集群部署支持",
            "多LLM提供商",
            "知识图谱可视化",
            "论文评审AI",
            "PDF在线阅读",
            "用户多租户系统"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
