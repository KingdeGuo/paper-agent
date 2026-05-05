"""Concept glossary: auto-extract and manage key terms from papers."""

import json
import logging
import uuid

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS concept_glossary (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
            term TEXT NOT NULL, definition TEXT, category TEXT,
            source_document_id TEXT, aliases TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        await session.commit()


@router.post("/glossary/extract", summary="Extract terms from a paper")
async def extract_terms(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Auto-extract key terms and definitions from a paper using AI."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Document not found"}
    text = (doc.abstract or "") + " " + (doc.summary or "") + " " + (doc.title or "")
    if len(text) < 50:
        return {"terms": [], "message": "Not enough text to extract terms"}

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Extract key technical terms and their definitions from this text. Output as JSON list: [{{\"term\": \"...\", \"definition\": \"...\", \"category\": \"methodology/technique/concept\"}}]\n\nText: {text[:2000]}"}],
            system_prompt="You are a terminology extraction system. Be precise. Output valid JSON only.",
        )
        content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
        # Find JSON in response
        import re
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        terms = json.loads(json_match.group()) if json_match else []
    except Exception:
        terms = []

    imported = []
    async with db.async_session_maker() as session:
        for t in terms[:20]:
            tid = str(uuid.uuid4())
            try:
                await session.execute(sa_text(
                    "INSERT INTO concept_glossary (id, user_id, term, definition, category, source_document_id) VALUES (:id, 'default', :t, :d, :c, :sid)"),
                    {"id": tid, "t": t.get("term", ""), "d": t.get("definition", ""),
                     "c": t.get("category", "concept"), "sid": document_id})
                imported.append(t.get("term", ""))
            except Exception:
                pass
        await session.commit()
    return {"extracted": len(imported), "terms": imported}


@router.get("/glossary", summary="Get glossary terms")
async def get_glossary(search: str = "", category: str = "", db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT * FROM concept_glossary WHERE user_id = 'default'"
        params = {}
        if search:
            sql += " AND (term LIKE :s OR definition LIKE :s)"
            params["s"] = f"%{search}%"
        if category:
            sql += " AND category = :c"
            params["c"] = category
        sql += " ORDER BY term ASC LIMIT 200"
        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{"id": r[0], "term": r[2], "definition": r[3], "category": r[4],
                 "source_document_id": r[5], "created_at": str(r[7])} for r in rows]


@router.put("/glossary/{term_id}", summary="Update glossary term")
async def update_term(term_id: str, definition: str = None, category: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    sets = []
    params = {"id": term_id}
    if definition: sets.append("definition = :d"); params["d"] = definition
    if category: sets.append("category = :c"); params["c"] = category
    if sets:
        async with db.async_session_maker() as session:
            await session.execute(sa_text(f"UPDATE concept_glossary SET {', '.join(sets)} WHERE id = :id"), params)
            await session.commit()
    return {"message": "Updated"}


@router.get("/glossary/categories", summary="Get glossary categories")
async def get_categories(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT category, COUNT(*) as cnt FROM concept_glossary WHERE user_id = 'default' GROUP BY category ORDER BY cnt DESC"))).fetchall()
        return [{"category": r[0] or "uncategorized", "count": r[1]} for r in rows]


@router.delete("/glossary/{term_id}", summary="Delete glossary term")
async def delete_term(term_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM concept_glossary WHERE id = :id"), {"id": term_id})
        await session.commit()
    return {"message": "Deleted"}
