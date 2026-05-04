"""System Health Dashboard — status of all subsystems at a glance."""

import logging
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_vector_service, get_llm_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/system-health", summary="Full system health check")
async def system_health(db=Depends(get_db), vector_service=Depends(get_vector_service)):
    """Check the health of all subsystems."""
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall": "healthy",
        "subsystems": {},
        "warnings": [],
    }

    # 1. Database
    try:
        if db:
            async with db.async_session_maker() as session:
                await session.execute(sa_text("SELECT 1"))
            health["subsystems"]["database"] = {"status": "healthy", "type": "SQLite/PostgreSQL"}
        else:
            health["subsystems"]["database"] = {"status": "unavailable"}
            health["warnings"].append("Database service not initialized")
    except Exception as e:
        health["subsystems"]["database"] = {"status": "error", "error": str(e)}
        health["warnings"].append(f"Database error: {e}")
        health["overall"] = "degraded"

    # 2. Vector DB
    try:
        if vector_service:
            stats = vector_service.get_collection_stats()
            health["subsystems"]["vector_db"] = {"status": "healthy", "chunks": stats.get("total_chunks", 0), "model": stats.get("model", "N/A")}
        else:
            health["subsystems"]["vector_db"] = {"status": "unavailable"}
            health["warnings"].append("Vector DB not initialized")
    except Exception as e:
        health["subsystems"]["vector_db"] = {"status": "error", "error": str(e)}

    # 3. LLM
    try:
        llm = get_llm_service()
        if llm and hasattr(llm, 'provider') and llm.provider:
            health["subsystems"]["llm"] = {"status": "available", "provider": llm.provider.__class__.__name__}
        else:
            health["subsystems"]["llm"] = {"status": "unconfigured"}
            health["warnings"].append("No LLM provider configured")
    except Exception as e:
        health["subsystems"]["llm"] = {"status": "error", "error": str(e)}

    # 4. arXiv
    try:
        from paper_agent.backend.services.arxiv_service import arxiv_service
        if arxiv_service:
            health["subsystems"]["arxiv"] = {"status": "available"}
        else:
            health["subsystems"]["arxiv"] = {"status": "unavailable"}
    except Exception as e:
        health["subsystems"]["arxiv"] = {"status": "error", "error": str(e)}

    # 5. External APIs
    apis = {}
    for name, url in [("CrossRef", "https://api.crossref.org"), ("Semantic Scholar", "https://api.semanticscholar.org")]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
                apis[name] = {"status": "reachable", "latency_ms": resp.elapsed.total_seconds() * 1000}
        except Exception as e:
            apis[name] = {"status": "unreachable", "error": str(e)}
    health["subsystems"]["external_apis"] = apis

    # 6. Data quality score
    try:
        async with db.async_session_maker() as session:
            doc_count = (await session.execute(sa_text("SELECT COUNT(*) FROM documents"))).scalar() or 0
            reading_count = (await session.execute(sa_text("SELECT COUNT(*) FROM reading_list"))).scalar() or 0
            flashcard_count = (await session.execute(sa_text("SELECT COUNT(*) FROM flashcards WHERE is_deleted = 0"))).scalar() or 0
            discussion_count = (await session.execute(sa_text("SELECT COUNT(*) FROM paper_discussions WHERE is_deleted = 0"))).scalar() or 0
            codex_count = (await session.execute(sa_text("SELECT COUNT(*) FROM codex_entries WHERE is_deleted = 0"))).scalar() or 0
            tree_nodes = (await session.execute(sa_text("SELECT COUNT(*) FROM directory_nodes WHERE is_deleted = 0"))).scalar() or 0

            health["data_volumes"] = {
                "documents": doc_count, "reading_list": reading_count,
                "flashcards": flashcard_count, "discussions": discussion_count,
                "codex_entries": codex_count, "literature_tree_nodes": tree_nodes,
            }
    except: pass

    # 7. Route count
    from backend.main import app
    route_count = len([r for r in app.routes if hasattr(r, "methods")])
    health["route_count"] = route_count
    health["subsystems"]["api"] = {"status": "healthy", "routes": route_count}

    # Determine overall
    errors = [s for s in health["subsystems"].values() if isinstance(s, dict) and s.get("status") == "error"]
    if errors:
        health["overall"] = "degraded"
    unavail = [s for s in health["subsystems"].values() if isinstance(s, dict) and s.get("status") == "unavailable"]
    if unavail and not errors:
        health["overall"] = "partial"

    return health
