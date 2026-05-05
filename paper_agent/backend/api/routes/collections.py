"""Paper collections: curated bundles for sharing and organization."""

import json
import logging
import uuid

from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS paper_collections (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL, description TEXT, is_public INTEGER DEFAULT 0,
                share_code TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS collection_papers (
                id TEXT PRIMARY KEY, collection_id TEXT NOT NULL,
                document_id TEXT NOT NULL, notes TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            await session.execute(sa_text(ddl))
        await session.commit()


@router.post("/collections", summary="Create a paper collection")
async def create_collection(title: str, description: str = "", is_public: bool = False, db=Depends(get_db)):
    await ensure_tables(db)
    cid = str(uuid.uuid4())
    share_code = str(uuid.uuid4())[:8] if is_public else None
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO paper_collections (id, user_id, title, description, is_public, share_code) VALUES (:id, 'default', :t, :d, :p, :sc)"),
            {"id": cid, "t": title, "d": description, "p": int(is_public), "sc": share_code})
        await session.commit()
    return {"id": cid, "title": title, "share_code": share_code}


@router.get("/collections", summary="List collections")
async def list_collections(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT c.*, (SELECT COUNT(*) FROM collection_papers WHERE collection_id = c.id) as paper_count FROM paper_collections c WHERE c.user_id = 'default' ORDER BY c.updated_at DESC"))).fetchall()
        return [{"id": r[0], "title": r[2], "description": r[3], "is_public": bool(r[4]),
                 "share_code": r[5], "paper_count": r[8] or 0} for r in rows]


@router.get("/collections/{collection_id}", summary="Get collection details")
async def get_collection(collection_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        col = (await session.execute(sa_text("SELECT * FROM paper_collections WHERE id = :id"), {"id": collection_id})).fetchone()
        if not col:
            raise HTTPException(status_code=404, detail="Collection not found")
        papers = (await session.execute(sa_text(
            "SELECT cp.*, d.title, d.authors, d.year, d.abstract FROM collection_papers cp "
            "LEFT JOIN documents d ON cp.document_id = d.id WHERE cp.collection_id = :cid ORDER BY cp.added_at DESC"),
            {"cid": collection_id})).fetchall()
        return {
            "id": col[0], "title": col[2], "description": col[3], "is_public": bool(col[4]),
            "share_code": col[5], "papers": [{
                "id": p[0], "document_id": p[2], "notes": p[3] or "",
                "title": p[5] or "Untitled", "authors": json.loads(p[6]) if isinstance(p[6], str) else (p[6] or []),
                "year": p[7], "abstract": (p[8] or "")[:200],
            } for p in papers],
        }


@router.post("/collections/{collection_id}/papers", summary="Add paper to collection")
async def add_to_collection(collection_id: str, document_id: str, notes: str = "", db=Depends(get_db)):
    await ensure_tables(db)
    pid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO collection_papers (id, collection_id, document_id, notes) VALUES (:id, :cid, :did, :n)"),
            {"id": pid, "cid": collection_id, "did": document_id, "n": notes})
        await session.commit()
    return {"id": pid, "collection_id": collection_id, "document_id": document_id}


@router.delete("/collections/{collection_id}/papers/{document_id}", summary="Remove paper from collection")
async def remove_from_collection(collection_id: str, document_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "DELETE FROM collection_papers WHERE collection_id = :cid AND document_id = :did"),
            {"cid": collection_id, "did": document_id})
        await session.commit()
    return {"message": "Removed"}


@router.get("/shared/{share_code}", summary="Access a shared collection")
async def get_shared_collection(share_code: str, db=Depends(get_db)):
    """Access a public collection via share code (no auth needed)."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        col = (await session.execute(sa_text(
            "SELECT * FROM paper_collections WHERE share_code = :sc AND is_public = 1"),
            {"sc": share_code})).fetchone()
        if not col:
            raise HTTPException(status_code=404, detail="Collection not found or not public")
        papers = (await session.execute(sa_text(
            "SELECT cp.*, d.title, d.authors, d.year FROM collection_papers cp "
            "LEFT JOIN documents d ON cp.document_id = d.id WHERE cp.collection_id = :cid"),
            {"cid": col[0]})).fetchall()
        return {
            "title": col[2], "description": col[3],
            "papers": [{"title": p[5] or "Untitled", "authors": json.loads(p[6]) if isinstance(p[6], str) else (p[6] or []),
                        "year": p[7]} for p in papers],
        }
