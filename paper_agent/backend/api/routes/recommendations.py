"""Smart recommendations and reading goals engine."""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_vector_service, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db: ClusterDatabaseService):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS reading_goals (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                goal_type TEXT NOT NULL, target INTEGER NOT NULL, period TEXT NOT NULL,
                progress INTEGER DEFAULT 0, start_date TEXT, end_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS reading_sessions (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                document_id TEXT, duration_minutes INTEGER DEFAULT 0,
                pages_read INTEGER DEFAULT 0, date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS paper_recommendations (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                document_id TEXT, reason TEXT, score FLOAT,
                recommendation_type TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_dismissed INTEGER DEFAULT 0
            )""",
        ]:
            await session.execute(sa_text(ddl))
        await session.commit()


# ─── Reading Goals ─────────────────────────────────────────

@router.post("/goals", summary="Set a reading goal")
async def set_reading_goal(
    goal_type: str = "papers_per_week",
    target: int = 5,
    period: str = "weekly",
    db: ClusterDatabaseService = Depends(get_db),
):
    """Set a reading goal (e.g., read 5 papers per week)."""
    await ensure_tables(db)
    gid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    end = (datetime.utcnow() + timedelta(days=7 if period == "weekly" else 30)).isoformat()

    async with db.async_session_maker() as session:
        # Deactivate existing goals of same type
        await session.execute(sa_text("UPDATE reading_goals SET is_active = 0 WHERE user_id = 'default' AND goal_type = :gt"),
                              {"gt": goal_type})
        await session.execute(sa_text(
            "INSERT INTO reading_goals (id, user_id, goal_type, target, period, progress, start_date, end_date) "
            "VALUES (:id, 'default', :gt, :target, :p, 0, :s, :e)"),
            {"id": gid, "gt": goal_type, "target": target, "p": period, "s": now, "e": end})
        await session.commit()
    return {"id": gid, "goal_type": goal_type, "target": target, "period": period}


@router.get("/goals", summary="Get reading goals")
async def get_reading_goals(db: ClusterDatabaseService = Depends(get_db)):
    """Get active reading goals with progress."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM reading_goals WHERE user_id = 'default' AND is_active = 1 ORDER BY created_at DESC"
        ))).fetchall()
        return [{
            "id": r[0], "goal_type": r[2], "target": r[3], "period": r[4],
            "progress": r[5] or 0, "start_date": str(r[6]) if r[6] else None,
            "end_date": str(r[7]) if r[7] else None,
            "percent": round(((r[5] or 0) / r[3]) * 100, 1) if r[3] > 0 else 0,
        } for r in rows]


@router.post("/log-session", summary="Log a reading session")
async def log_reading_session(
    document_id: Optional[str] = None,
    duration_minutes: int = 15,
    pages_read: int = 0,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Log a reading session for progress tracking."""
    await ensure_tables(db)
    sid = str(uuid.uuid4())
    today = datetime.utcnow().strftime("%Y-%m-%d")

    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO reading_sessions (id, user_id, document_id, duration_minutes, pages_read, date) "
            "VALUES (:id, 'default', :did, :dur, :p, :d)"),
            {"id": sid, "did": document_id, "dur": duration_minutes, "p": pages_read, "d": today})

        # Update goal progress (papers_read)
        await session.execute(sa_text(
            "UPDATE reading_goals SET progress = progress + 1 "
            "WHERE user_id = 'default' AND is_active = 1 AND goal_type = 'papers_per_week'"))
        await session.commit()
    return {"id": sid, "logged": True, "date": today}


@router.get("/session-stats", summary="Get reading session stats")
async def get_session_stats(days: int = 30, db: ClusterDatabaseService = Depends(get_db)):
    """Get reading statistics over a period."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT date, COUNT(*), SUM(duration_minutes), SUM(pages_read) FROM reading_sessions "
            "WHERE user_id = 'default' AND date >= :d GROUP BY date ORDER BY date"),
            {"d": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")})).fetchall()
    total_minutes = sum(r[2] or 0 for r in rows)
    total_pages = sum(r[3] or 0 for r in rows)

    return {
        "total_sessions": sum(r[1] for r in rows),
        "total_minutes": total_minutes,
        "total_pages": total_pages,
        "avg_minutes_per_session": round(total_minutes / max(len(rows), 1), 1),
        "daily": [{"date": r[0], "sessions": r[1], "minutes": r[2] or 0, "pages": r[3] or 0} for r in rows],
    }


# ─── Smart Recommendations ────────────────────────────────

@router.get("/suggestions", summary="Get paper recommendations")
async def get_recommendations(
    limit: int = 5,
    db: ClusterDatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Get smart paper recommendations based on library content and reading history."""
    await ensure_tables(db)

    # Get recently read papers for context
    async with db.async_session_maker() as session:
        read_ids = (await session.execute(sa_text(
            "SELECT document_id FROM reading_list WHERE user_id = 'default' AND status = 'read' ORDER BY date_updated DESC LIMIT 3"
        ))).fetchall()
        read_ids = [r[0] for r in read_ids]

    # Get unread papers in library
    all_docs = await db.get_documents(limit=50, user_id="default") if hasattr(db, 'get_documents') else await db.get_all_documents(limit=50)

    # Simple recommender: find papers similar to recently read ones
    recommendations = []
    seen_ids = set()

    if vector_service and read_ids:
        for rid in read_ids:
            doc = await db.get_document(rid)
            if doc:
                text = (doc.abstract or doc.title or "")
                results = vector_service.search_similar(text, limit=limit + 1)
                for r in results:
                    did = r.get("document_id")
                    if did and did not in seen_ids and did not in read_ids:
                        seen_ids.add(did)
                        recommendations.append({
                            "document_id": did,
                            "score": r.get("score", 0),
                            "reason": "Similar to papers you've read",
                        })

    # Fallback: recommend unread papers
    if len(recommendations) < limit:
        for doc in all_docs:
            if doc.id not in seen_ids and doc.id not in read_ids:
                seen_ids.add(doc.id)
                recommendations.append({
                    "document_id": doc.id,
                    "score": 0.5,
                    "reason": "Unread paper in your library",
                })
            if len(recommendations) >= limit:
                break

    # Enrich with document details
    enriched = []
    for rec in recommendations[:limit]:
        doc = await db.get_document(rec["document_id"])
        if doc:
            enriched.append({
                "id": doc.id,
                "title": doc.title or doc.filename,
                "authors": doc.authors or [],
                "year": doc.year,
                "abstract": (doc.abstract or "")[:200],
                "score": rec["score"],
                "reason": rec["reason"],
            })

    # Save recommendations
    async with db.async_session_maker() as session:
        for rec in enriched:
            await session.execute(sa_text(
                "INSERT INTO paper_recommendations (id, user_id, document_id, reason, score, recommendation_type) "
                "VALUES (:id, 'default', :did, :r, :s, 'smart')"),
                {"id": str(uuid.uuid4()), "did": rec["id"], "r": rec["reason"], "s": rec["score"]})
        await session.commit()

    return {"recommendations": enriched, "based_on": len(read_ids), "total_in_library": len(all_docs)}


# ─── Trend Analysis ────────────────────────────────────────

@router.get("/trends", summary="Analyze research trends")
async def analyze_trends(
    db: ClusterDatabaseService = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Analyze research trends and emerging topics in your library."""
    docs = await db.get_documents(limit=50, user_id="default") if hasattr(db, 'get_documents') else await db.get_all_documents(limit=50)
    if not docs:
        return {"trends": [], "message": "Not enough papers for trend analysis"}

    # Aggregate by year
    years = {}
    for d in docs:
        y = d.year or 0
        if y not in years:
            years[y] = []
        years[y].append(d.title or d.filename)

    # Get keyword frequency
    keywords = {}
    for d in docs:
        for k in (d.keywords or []):
            keywords[k] = keywords.get(k, 0) + 1

    top_keywords = sorted(keywords.items(), key=lambda x: -x[1])[:20]

    # Get trending topics (keywords growing in recent years)
    recent_docs = [d for d in docs if (d.year or 0) >= 2023]
    recent_keywords = {}
    for d in recent_docs:
        for k in (d.keywords or []):
            recent_keywords[k] = recent_keywords.get(k, 0) + 1
    trending_keywords = sorted(recent_keywords.items(), key=lambda x: -x[1])[:10]

    return {
        "total_papers": len(docs),
        "year_range": {"min": min(years.keys()) if years else None, "max": max(years.keys()) if years else None},
        "papers_by_year": {str(y): len(v) for y, v in sorted(years.items())},
        "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
        "trending_keywords": [{"keyword": k, "count": v} for k, v in trending_keywords],
        "recent_papers": len(recent_docs),
    }
