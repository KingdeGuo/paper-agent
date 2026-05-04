"""Paper Hub — consolidated view of everything about a paper from all subsystems."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_vector_service, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/paper-hub/{document_id}", summary="Consolidated paper view")
async def get_paper_hub(document_id: str, db=Depends(get_db)):
    """Get everything about a paper: metadata, summary, discussions, flashcards,
    codex entries, literature tree location, reading status, impact, annotations."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    hub = {
        "document": {
            "id": doc.id, "title": doc.title or doc.filename,
            "authors": doc.authors or [], "year": doc.year,
            "abstract": doc.abstract, "summary": doc.summary,
            "keywords": doc.keywords or [], "processed": doc.processed,
            "arxiv_id": getattr(doc, "arxiv_id", None),
        },
        "meta": (doc.doc_metadata or {}),
    }

    # 1. Reading status
    try:
        async with db.async_session_maker() as session:
            row = (await session.execute(sa_text(
                "SELECT status, progress, current_page, total_pages FROM reading_list WHERE document_id = :did AND user_id = 'default'"),
                {"did": document_id})).fetchone()
            if row:
                hub["reading"] = {"status": row[0], "progress": row[1], "current_page": row[2], "total_pages": row[3]}
    except: pass

    # 2. Discussion count
    try:
        async with db.async_session_maker() as session:
            hub["discussion_count"] = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM paper_discussions WHERE document_id = :did AND is_deleted = 0"),
                {"did": document_id})).scalar() or 0
    except: pass

    # 3. Flashcard count
    try:
        async with db.async_session_maker() as session:
            hub["flashcard_count"] = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM flashcards WHERE document_id = :did AND is_deleted = 0"),
                {"did": document_id})).scalar() or 0
            due = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM flashcards WHERE document_id = :did AND is_deleted = 0 AND (next_review IS NULL OR next_review <= :now)"),
                {"did": document_id, "now": __import__('datetime').datetime.utcnow().isoformat()})).scalar() or 0
            hub["flashcard_due"] = due
    except: pass

    # 4. Codex entries
    try:
        async with db.async_session_maker() as session:
            codex = (await session.execute(sa_text(
                "SELECT id, title, entry_type, importance FROM codex_entries WHERE source_document_id = :did AND is_deleted = 0 ORDER BY importance DESC"),
                {"did": document_id})).fetchall()
            hub["codex_entries"] = [{"id": c[0], "title": c[1], "type": c[2], "importance": c[3]} for c in codex]
    except: pass

    # 5. Literature Tree location
    try:
        async with db.async_session_maker() as session:
            tree_nodes = (await session.execute(sa_text(
                "SELECT dn.id, dn.name, dn.icon, dn.node_type FROM directory_papers dp "
                "JOIN directory_nodes dn ON dp.node_id = dn.id WHERE dp.document_id = :did"),
                {"did": document_id})).fetchall()
            hub["tree_locations"] = [{"id": t[0], "name": t[1], "icon": t[2], "type": t[3]} for t in tree_nodes]
    except: pass

    # 6. Annotations count
    try:
        async with db.async_session_maker() as session:
            hub["annotation_count"] = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM annotations WHERE document_id = :did AND is_deleted = 0"),
                {"did": document_id})).scalar() or 0
    except: pass

    # 7. Impact metrics
    meta = doc.doc_metadata or {}
    impact = meta.get("impact", {})
    hub["impact"] = {
        "citation_count": impact.get("citation_count", 0),
        "influential_citations": impact.get("influential_citations", 0),
        "influence_score": impact.get("influence_score", 0),
    }

    # 8. Recent activity
    try:
        async with db.async_session_maker() as session:
            activity = (await session.execute(sa_text(
                "SELECT description, created_at FROM workspace_activity WHERE document_id = :did ORDER BY created_at DESC LIMIT 5"),
                {"did": document_id})).fetchall()
            hub["recent_activity"] = [{"description": a[0], "date": str(a[1])[:10] if a[1] else None} for a in activity]
    except: pass

    # 9. Library matrix data
    try:
        async with db.async_session_maker() as session:
            matrix = (await session.execute(sa_text(
                "SELECT dimensions FROM literature_matrix WHERE document_id = :did AND user_id = 'default'"),
                {"did": document_id})).fetchone()
            hub["matrix_dimensions"] = json.loads(matrix[0]) if matrix and matrix[0] else {}
    except: pass

    return hub


@router.get("/paper-hub/batch", summary="Batch paper hub data")
async def batch_paper_hub(document_ids: str, db=Depends(get_db)):
    """Get summary data for multiple papers at once (for list views)."""
    ids = [d.strip() for d in document_ids.split(",") if d.strip()]
    results = []
    for did in ids[:20]:
        doc = await db.get_document(did)
        if not doc:
            continue
        entry = {"id": did, "title": doc.title or doc.filename, "authors": doc.authors or [], "year": doc.year}

        try:
            async with db.async_session_maker() as session:
                status = (await session.execute(sa_text(
                    "SELECT status FROM reading_list WHERE document_id = :did AND user_id = 'default'"),
                    {"did": did})).fetchone()
                if status: entry["reading_status"] = status[0]
                entry["discussions"] = (await session.execute(sa_text(
                    "SELECT COUNT(*) FROM paper_discussions WHERE document_id = :did AND is_deleted = 0"),
                    {"did": did})).scalar() or 0
        except: pass
        results.append(entry)

    return {"papers": results, "count": len(results)}
