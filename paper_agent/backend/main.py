"""
Paper Agent - 企业级文献管理系统
完整后端实现
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ── Import compatibility: map 'backend.xxx' → 'paper_agent.backend.xxx' ──
import importlib.abc
import importlib.machinery

class _BackendCompat(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith('backend') or fullname == 'backend':
            mapped = 'paper_agent.' + fullname
            try:
                if mapped not in sys.modules:
                    importlib.import_module(mapped)
                # Return a spec pointing to the already-loaded module
                mod = sys.modules[mapped]
                spec = importlib.machinery.ModuleSpec(fullname, importlib.machinery.BuiltinImporter())
                # Make the module available under the short name too
                sys.modules[fullname] = mod
                return spec
            except ImportError:
                pass
        return None

if not any(isinstance(f, _BackendCompat) for f in sys.meta_path):
    sys.meta_path.insert(0, _BackendCompat())
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import time

from backend.middleware.audit import AuditMiddleware

# ── Ensure database models are loaded first ──
import warnings
warnings.filterwarnings("ignore", message="This declarative base already contains a class")
warnings.filterwarnings("ignore", message="Table .* is already defined")

import backend.services.cluster_database as _cd
import backend.models.user as _um
import backend.models.notebook as _nm

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
            try:
                db.create_tables()
                logger.info("Database tables verified")
            except Exception as table_err:
                logger.warning(f"Table creation note: {table_err}")
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
        review, arxiv, notebooks, discovery, zotero, drafting, 
        annotations, bibtex, citations, reading, ask, collaboration, 
        digest, overleaf, stats, search_saved, import_documents, recommendations,
        alerts, projects, glossary, dedup, collections, tagging, timeline,
        extraction, digest_email, workspace_routes, integrations, peer_review, research_assistant,
        literature_matrix, citation_chain, conference_tracker, research_codex, reading_analytics,
        chat_session, methodology_critic, paper_presentation, research_journal, flashcard_system,
        literature_tree, scholar_perspectives,
        notification_center, multi_source_search, metadata_enhance, impact_tracker,
        paper_hub, unified_search, data_quality, system_health, onboarding,
        graphrag_routes, agent_routes, rerank_routes, multi_modal, dspy_integration,
        scraper_routes, skills_marketplace, bot_routes, memory_routes, figure_routes,
        downstream_routes, core_routes,
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
    app.include_router(citations.router, prefix="/api/citations", tags=["citations"])
    app.include_router(reading.router, prefix="/api/reading", tags=["reading"])
    app.include_router(ask.router, prefix="/api/ask", tags=["ask"])
    app.include_router(collaboration.router, prefix="/api/collab", tags=["collaboration"])
    app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
    app.include_router(overleaf.router, prefix="/api/overleaf", tags=["overleaf"])
    app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
    app.include_router(search_saved.router, prefix="/api/searches", tags=["searches"])
    app.include_router(import_documents.router, prefix="/api/import", tags=["import"])
    app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
    app.include_router(alerts.router, prefix="/api", tags=["alerts"])
    app.include_router(projects.router, prefix="/api", tags=["projects"])
    app.include_router(glossary.router, prefix="/api", tags=["glossary"])
    app.include_router(dedup.router, prefix="/api/dedup", tags=["dedup"])
    app.include_router(collections.router, prefix="/api", tags=["collections"])
    app.include_router(tagging.router, prefix="/api/tags", tags=["tagging"])
    app.include_router(timeline.router, prefix="/api", tags=["timeline"])
    app.include_router(extraction.router, prefix="/api", tags=["extraction"])
    app.include_router(digest_email.router, prefix="/api", tags=["digest"])
    app.include_router(workspace_routes.router, prefix="/api", tags=["workspace"])
    app.include_router(integrations.router, prefix="/api", tags=["integrations"])
    app.include_router(peer_review.router, prefix="/api", tags=["peer-review"])
    app.include_router(research_assistant.router, prefix="/api", tags=["research-assistant"])
    app.include_router(literature_matrix.router, prefix="/api", tags=["literature-matrix"])
    app.include_router(citation_chain.router, prefix="/api", tags=["citation-chain"])
    app.include_router(conference_tracker.router, prefix="/api", tags=["conferences"])
    app.include_router(research_codex.router, prefix="/api", tags=["research-codex"])
    app.include_router(reading_analytics.router, prefix="/api", tags=["reading-analytics"])
    app.include_router(chat_session.router, prefix="/api", tags=["chat"])
    app.include_router(methodology_critic.router, prefix="/api", tags=["methodology-critic"])
    app.include_router(paper_presentation.router, prefix="/api", tags=["presentations"])
    app.include_router(research_journal.router, prefix="/api", tags=["journal"])
    app.include_router(flashcard_system.router, prefix="/api", tags=["flashcards"])
    app.include_router(literature_tree.router, prefix="/api", tags=["literature-tree"])
    app.include_router(scholar_perspectives.router, prefix="/api", tags=["scholar-perspectives"])
    app.include_router(notification_center.router, prefix="/api", tags=["notifications"])
    app.include_router(multi_source_search.router, prefix="/api", tags=["multi-source-search"])
    app.include_router(metadata_enhance.router, prefix="/api", tags=["metadata"])
    app.include_router(impact_tracker.router, prefix="/api", tags=["impact"])
    app.include_router(paper_hub.router, prefix="/api", tags=["paper-hub"])
    app.include_router(unified_search.router, prefix="/api", tags=["unified-search"])
    app.include_router(data_quality.router, prefix="/api", tags=["data-quality"])
    app.include_router(system_health.router, prefix="/api", tags=["system-health"])
    app.include_router(onboarding.router, prefix="/api", tags=["onboarding"])
    app.include_router(graphrag_routes.router, prefix="/api", tags=["graphrag"])
    app.include_router(agent_routes.router, prefix="/api", tags=["agents"])
    app.include_router(rerank_routes.router, prefix="/api", tags=["rerank"])
    app.include_router(multi_modal.router, prefix="/api", tags=["multi-modal"])
    app.include_router(dspy_integration.router, prefix="/api", tags=["dspy"])
    app.include_router(scraper_routes.router, prefix="/api", tags=["scraper"])
    app.include_router(skills_marketplace.router, prefix="/api", tags=["skills"])
    app.include_router(bot_routes.router, prefix="/api", tags=["bot"])
    app.include_router(memory_routes.router, prefix="/api", tags=["memory"])
    app.include_router(figure_routes.router, prefix="/api", tags=["figures"])
    app.include_router(downstream_routes.router, prefix="/api", tags=["downstream"])
    app.include_router(core_routes.router, prefix="/api", tags=["research"])
    logger.info("✓ 73个路由模块已加载 — Full Research Pipeline")
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
