"""Research Codex — personal knowledge base built from paper annotations and insights."""

import json
import logging
import uuid
from datetime import datetime
from typing import List

from backend.services.registry import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS codex_entries (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                title TEXT NOT NULL, content TEXT, entry_type TEXT DEFAULT 'note',
                source_document_id TEXT, tags TEXT DEFAULT '[]',
                references TEXT DEFAULT '[]', importance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS codex_connections (
                id TEXT PRIMARY KEY, source_entry_id TEXT NOT NULL,
                target_entry_id TEXT NOT NULL, connection_type TEXT DEFAULT 'related',
                description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS codex_insights (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                content TEXT NOT NULL, insight_type TEXT DEFAULT 'insight',
                source_entry_ids TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except Exception: pass
        await session.commit()


# ─── Entries ───────────────────────────────────────────────

@router.post("/codex/entries", summary="Create codex entry")
async def create_entry(title: str, content: str = "", entry_type: str = "note",
                        source_document_id: str = None, tags: List[str] = None,
                        importance: int = 0, db=Depends(get_db)):
    """Create a knowledge entry in your research codex."""
    await ensure_tables(db)
    eid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO codex_entries (id, user_id, title, content, entry_type, source_document_id, tags, importance) "
            "VALUES (:id, 'default', :t, :c, :et, :sd, :tg, :imp)"),
            {"id": eid, "t": title, "c": content, "et": entry_type,
             "sd": source_document_id, "tg": json.dumps(tags or []), "imp": importance})
        await session.commit()
    return {"id": eid, "title": title, "type": entry_type}


@router.get("/codex/entries", summary="List codex entries")
async def list_entries(entry_type: str = None, tag: str = None,
                        search: str = None, importance_min: int = None,
                        db=Depends(get_db)):
    """Search and filter codex entries with full-text search."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT * FROM codex_entries WHERE user_id = 'default' AND is_deleted = 0"
        params = {}
        if entry_type:
            sql += " AND entry_type = :et"
            params["et"] = entry_type
        if tag:
            sql += " AND tags LIKE :tg"
            params["tg"] = f'%"{tag}"%'
        if search:
            sql += " AND (title LIKE :s OR content LIKE :s)"
            params["s"] = f"%{search}%"
        if importance_min is not None:
            sql += " AND importance >= :imp"
            params["imp"] = importance_min
        sql += " ORDER BY importance DESC, updated_at DESC LIMIT 100"

        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{
            "id": r[0], "title": r[2], "content": (r[3] or "")[:500],
            "entry_type": r[4], "source_document_id": r[5],
            "tags": json.loads(r[6]) if isinstance(r[6], str) else (r[6] or []),
            "importance": r[8] or 0,
            "created_at": str(r[9]) if r[9] else None,
            "updated_at": str(r[10]) if r[10] else None,
        } for r in rows]


@router.get("/codex/entries/{entry_id}", summary="Get codex entry detail")
async def get_entry(entry_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        row = (await session.execute(sa_text(
            "SELECT * FROM codex_entries WHERE id = :id AND is_deleted = 0"),
            {"id": entry_id})).fetchone()
        if not row:
            return {"error": "Entry not found"}
        return {
            "id": row[0], "title": row[2], "content": row[3],
            "entry_type": row[4], "source_document_id": row[5],
            "tags": json.loads(row[6]) if isinstance(row[6], str) else (row[6] or []),
            "references": json.loads(row[7]) if isinstance(row[7], str) else (row[7] or []),
            "importance": row[8] or 0,
            "created_at": str(row[9]) if row[9] else None,
            "updated_at": str(row[10]) if row[10] else None,
        }


@router.put("/codex/entries/{entry_id}", summary="Update codex entry")
async def update_entry(entry_id: str, content: str = None, title: str = None,
                        importance: int = None, tags: List[str] = None, db=Depends(get_db)):
    await ensure_tables(db)
    sets = ["updated_at = :n"]
    params = {"id": entry_id, "n": datetime.utcnow().isoformat()}
    if content is not None: sets.append("content = :c"); params["c"] = content
    if title is not None: sets.append("title = :t"); params["t"] = title
    if importance is not None: sets.append("importance = :i"); params["i"] = importance
    if tags is not None: sets.append("tags = :tg"); params["tg"] = json.dumps(tags)
    async with db.async_session_maker() as session:
        await session.execute(sa_text(f"UPDATE codex_entries SET {', '.join(sets)} WHERE id = :id"), params)
        await session.commit()
    return {"message": "Updated"}


@router.delete("/codex/entries/{entry_id}", summary="Delete codex entry")
async def delete_entry(entry_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE codex_entries SET is_deleted = 1 WHERE id = :id"), {"id": entry_id})
        await session.commit()
    return {"message": "Deleted"}


# ─── Connections ────────────────────────────────────────────

@router.post("/codex/connect", summary="Connect two codex entries")
async def connect_entries(source_entry_id: str, target_entry_id: str,
                           connection_type: str = "related", description: str = "", db=Depends(get_db)):
    await ensure_tables(db)
    cid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO codex_connections (id, source_entry_id, target_entry_id, connection_type, description) "
            "VALUES (:id, :sid, :tid, :ct, :d)"),
            {"id": cid, "sid": source_entry_id, "tid": target_entry_id, "ct": connection_type, "d": description})
        await session.commit()
    return {"id": cid, "message": "Connected"}


@router.get("/codex/graph/{entry_id}", summary="Get entry connection graph")
async def get_connection_graph(entry_id: str, db=Depends(get_db)):
    """Get all connected entries for knowledge graph visualization."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        entry = (await session.execute(sa_text(
            "SELECT id, title, entry_type FROM codex_entries WHERE id = :id"), {"id": entry_id})).fetchone()
        if not entry:
            return {"error": "Entry not found"}

        connections = (await session.execute(sa_text(
            "SELECT * FROM codex_connections WHERE source_entry_id = :eid OR target_entry_id = :eid"),
            {"eid": entry_id})).fetchall()

        related_ids = set()
        for c in connections:
            related_ids.add(c[1])
            related_ids.add(c[2])

        nodes = [{"id": entry[0], "title": entry[1], "type": entry[2], "center": True}]
        for rid in related_ids:
            if rid != entry_id:
                r = (await session.execute(sa_text(
                    "SELECT id, title, entry_type FROM codex_entries WHERE id = :id"), {"id": rid})).fetchone()
                if r:
                    nodes.append({"id": r[0], "title": r[1], "type": r[2], "center": False})

        edges = [{"source": c[1], "target": c[2], "type": c[3], "description": c[4]} for c in connections]

        return {"nodes": nodes, "edges": edges, "count": len(nodes)}


# ─── Auto-Insights ─────────────────────────────────────────

@router.post("/codex/auto-import", summary="Auto-import annotations into codex")
async def auto_import_annotations(document_id: str = None, db=Depends(get_db)):
    """Auto-import paper annotations and notes into the research codex."""
    await ensure_tables(db)
    imported = 0

    async with db.async_session_maker() as session:
        # Get annotations
        sql = "SELECT id, document_id, text, note, page_number FROM annotations WHERE is_deleted = 0"
        params = {}
        if document_id:
            sql += " AND document_id = :did"
            params["did"] = document_id
        annotations = (await session.execute(sa_text(sql), params)).fetchall()

        for a in annotations:
            content = a[2] or ""
            if a[3]:
                content += f"\n\nNote: {a[3]}"
            if not content.strip():
                continue

            # Check if already imported
            existing = (await session.execute(sa_text(
                "SELECT id FROM codex_entries WHERE source_document_id = :sid AND content = :c AND entry_type = 'annotation'"),
                {"sid": a[1], "c": content[:200]})).fetchone()
            if not existing:
                await session.execute(sa_text(
                    "INSERT INTO codex_entries (id, user_id, title, content, entry_type, source_document_id) "
                    "VALUES (:id, 'default', :t, :c, 'annotation', :sid)"),
                    {"id": str(uuid.uuid4()), "t": f"Annotation on page {a[4] or '?'}",
                     "c": content, "sid": a[1]})
                imported += 1

        await session.commit()

    return {"imported": imported, "message": f"Imported {imported} annotations into codex"}
