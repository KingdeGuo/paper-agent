"""Saved searches and search history API."""

import json
import logging
import uuid

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.registry import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_table(db: ClusterDatabaseService):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                name TEXT NOT NULL, query TEXT NOT NULL,
                filters TEXT DEFAULT '{}', result_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await session.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS search_history (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                query TEXT NOT NULL, result_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await session.commit()


@router.post("/save", summary="Save a search query")
async def save_search(
    name: str, query: str, filters: str = "{}", result_count: int = 0,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Save a search for later use."""
    await ensure_table(db)
    sid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO saved_searches (id, user_id, name, query, filters, result_count) VALUES (:id, 'default', :name, :q, :f, :rc)"
        ), {"id": sid, "name": name, "q": query, "f": filters, "rc": result_count})
        await session.commit()
    return {"id": sid, "name": name, "query": query}


@router.get("/saved", summary="List saved searches")
async def list_saved_searches(db: ClusterDatabaseService = Depends(get_db)):
    await ensure_table(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM saved_searches WHERE user_id = 'default' ORDER BY created_at DESC LIMIT 50"
        ))).fetchall()
        return [{"id": r[0], "name": r[2], "query": r[3], "filters": json.loads(r[4]) if isinstance(r[4], str) else r[4],
                 "result_count": r[5] or 0, "created_at": str(r[6])} for r in rows]


@router.delete("/saved/{search_id}", summary="Delete saved search")
async def delete_saved_search(search_id: str, db: ClusterDatabaseService = Depends(get_db)):
    await ensure_table(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM saved_searches WHERE id = :id"), {"id": search_id})
        await session.commit()
    return {"message": "Deleted"}


@router.post("/history", summary="Log search to history")
async def log_search(query: str, result_count: int = 0, db: ClusterDatabaseService = Depends(get_db)):
    await ensure_table(db)
    hid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO search_history (id, user_id, query, result_count) VALUES (:id, 'default', :q, :rc)"
        ), {"id": hid, "q": query, "rc": result_count})
        await session.commit()
    return {"id": hid}


@router.get("/history", summary="Get search history")
async def get_search_history(limit: int = 20, db: ClusterDatabaseService = Depends(get_db)):
    await ensure_table(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM search_history WHERE user_id = 'default' ORDER BY created_at DESC LIMIT :lim"
        ), {"lim": limit})).fetchall()
        return [{"id": r[0], "query": r[2], "result_count": r[3] or 0, "created_at": str(r[4])} for r in rows]


@router.delete("/history", summary="Clear search history")
async def clear_search_history(db: ClusterDatabaseService = Depends(get_db)):
    await ensure_table(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM search_history WHERE user_id = 'default'"))
        await session.commit()
    return {"message": "History cleared"}
