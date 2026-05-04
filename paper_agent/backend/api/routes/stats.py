"""Consolidated dashboard stats and insights API."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_vector_service, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/full", summary="Get full dashboard stats")
async def get_full_stats(
    db: ClusterDatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Get comprehensive dashboard statistics and insights."""
    doc_stats = await db.get_processing_stats("default") if hasattr(db, 'get_processing_stats') else {}
    vector_stats = vector_service.get_collection_stats() if vector_service else {}

    reading_stats = {"total": 0, "to_read": 0, "reading": 0, "read_count": 0, "avg_progress": 0}
    recent_activity = []
    recent_docs = []

    try:
        reading_result = await _get_reading_stats(db)
        if reading_result:
            reading_stats = reading_result
    except Exception as e:
        logger.debug(f"Reading stats unavailable: {e}")

    try:
        recent_activity = await _get_recent_activity(db)
    except Exception as e:
        logger.debug(f"Activity unavailable: {e}")

    try:
        recent_docs = await _get_recent_docs(db)
    except Exception as e:
        logger.debug(f"Recent docs unavailable: {e}")

    return {
        "documents": {
            "total": doc_stats.get("total", 0),
            "pending": doc_stats.get("pending", 0),
            "processing": doc_stats.get("processing", 0),
            "completed": doc_stats.get("completed", 0),
            "failed": doc_stats.get("failed", 0),
        },
        "vector_db": vector_stats,
        "reading": reading_stats,
        "activity": recent_activity[:10],
        "recent_docs": recent_docs[:5],
    }


@router.get("/quick-insight", summary="Get AI quick insight")
async def get_quick_insight(
    db: ClusterDatabaseService = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate an AI-powered quick insight about the library."""
    docs = await db.get_documents(limit=10, user_id="default") if hasattr(db, 'get_documents') else []
    if not docs:
        return {"insight": "Upload papers to get AI-powered insights about your research library."}

    titles = "\n".join(f"- {d.title or d.filename} ({d.year or 'n.d.'})" for d in docs)
    try:
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Based on these papers in my library, give me one quick research insight or trend observation (1-2 sentences):\n\n{titles}"}],
            system_prompt="You are a research analyst. Be concise, insightful. Max 2 sentences.",
        )
        return {"insight": response.get("content", "AI insight unavailable."), "based_on": len(docs)}
    except Exception:
        return {"insight": "AI insight unavailable. Check your LLM configuration.", "based_on": 0}


async def _get_reading_stats(db):
    reading_result = {}
    async with db.async_session_maker() as session:
        row = (await session.execute(sa_text("""
            SELECT COUNT(*), SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status='read' THEN 1 ELSE 0 END),
                   AVG(progress)
            FROM reading_list WHERE user_id = 'default'
        """))).fetchone()
        if row:
            reading_result = {
                "total": row[0] or 0, "to_read": row[1] or 0,
                "reading": row[2] or 0, "read_count": row[3] or 0,
                "avg_progress": round(row[4] or 0, 2),
            }
    return reading_result


async def _get_recent_activity(db):
    try:
        async with db.async_session_maker() as session:
            rows = (await session.execute(sa_text("""
                SELECT * FROM activity_feed WHERE user_id = 'default'
                ORDER BY created_at DESC LIMIT 10
            """))).fetchall()
            return [{"id": r[0], "type": r[3], "description": r[4], "created_at": str(r[6])} for r in rows]
    except Exception:
        return []


async def _get_recent_docs(db):
    docs = await db.get_documents(limit=5, user_id="default") if hasattr(db, 'get_documents') else await db.get_all_documents(limit=5)
    from datetime import datetime as dt
    return [{
        "id": d.id, "title": d.title or d.filename, "authors": d.authors or [],
        "year": d.year, "processed": d.processed,
    } for d in docs]
