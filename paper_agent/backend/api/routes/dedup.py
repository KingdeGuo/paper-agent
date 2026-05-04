"""Duplicate detection and merging for papers."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_vector_service
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/detect", summary="Detect duplicate papers")
async def detect_duplicates(db=Depends(get_db), threshold: float = 0.85):
    """Detect potential duplicate papers using title similarity."""
    docs = await db.get_documents(limit=200) if db else []
    if not docs:
        return {"duplicates": []}

    # Simple title-based dedup using token overlap
    duplicates = []
    seen = set()
    for i, d1 in enumerate(docs):
        if d1.id in seen:
            continue
        t1 = set((d1.title or "").lower().split())
        if len(t1) < 3:
            continue
        for j, d2 in enumerate(docs):
            if j <= i or d2.id in seen:
                continue
            t2 = set((d2.title or "").lower().split())
            if len(t2) < 3:
                continue
            intersection = t1 & t2
            union = t1 | t2
            score = len(intersection) / len(union) if union else 0
            if score >= threshold:
                duplicates.append({
                    "score": round(score, 3),
                    "paper_a": {"id": d1.id, "title": d1.title or d1.filename, "authors": d1.authors or [], "year": d1.year},
                    "paper_b": {"id": d2.id, "title": d2.title or d2.filename, "authors": d2.authors or [], "year": d2.year},
                })
                seen.add(d2.id)
        seen.add(d1.id)

    return {"total_checked": len(docs), "duplicates_found": len(duplicates), "duplicates": duplicates}


@router.post("/merge", summary="Merge duplicate papers")
async def merge_papers(keep_id: str, remove_id: str, db=Depends(get_db)):
    """Merge two duplicate papers. Keep one, transfer annotations/notes from the other."""
    keep = await db.get_document(keep_id)
    remove = await db.get_document(remove_id)
    if not keep or not remove:
        raise HTTPException(status_code=404, detail="One or both papers not found")

    async with db.async_session_maker() as session:
        # Transfer annotations
        await session.execute(sa_text(
            "UPDATE annotations SET document_id = :keep WHERE document_id = :remove AND is_deleted = 0"),
            {"keep": keep_id, "remove": remove_id})
        # Transfer notes
        await session.execute(sa_text(
            "UPDATE document_notes SET document_id = :keep WHERE document_id = :remove AND is_deleted = 0"),
            {"keep": keep_id, "remove": remove_id})
        # Transfer reading list entries
        await session.execute(sa_text(
            "UPDATE reading_list SET document_id = :keep WHERE document_id = :remove"),
            {"keep": keep_id, "remove": remove_id})
        # Transfer notebook entries
        await session.execute(sa_text(
            "UPDATE notebook_entries SET document_id = :keep WHERE document_id = :remove"),
            {"keep": keep_id, "remove": remove_id})
        # Transfer project papers
        await session.execute(sa_text(
            "UPDATE project_papers SET document_id = :keep WHERE document_id = :remove"),
            {"keep": keep_id, "remove": remove_id})
        # Delete the duplicate document
        await session.execute(sa_text("DELETE FROM documents WHERE id = :id"), {"id": remove_id})
        await session.commit()

    # Remove from vector DB
    from backend.services.registry import get_vector_service
    vs = get_vector_service()
    if vs:
        vs.delete_document(remove_id)

    return {"message": "Papers merged", "kept": keep_id, "removed": remove_id,
            "kept_title": keep.title or keep.filename, "removed_title": remove.title or remove.filename}


@router.post("/auto-clean", summary="Auto-detect and merge all duplicates")
async def auto_clean_duplicates(db=Depends(get_db)):
    """Auto-detect and merge all duplicates, keeping the most complete version."""
    result = await detect_duplicates(db=db)
    merged = 0
    for dup in result.get("duplicates", []):
        a, b = dup["paper_a"], dup["paper_b"]
        # Keep the one with more metadata
        a_score = (1 if a.get("abstract") else 0) + (1 if a.get("year") else 0) + len(a.get("authors", []))
        b_score = (1 if b.get("abstract") else 0) + (1 if b.get("year") else 0) + len(b.get("authors", []))
        keep_id = a["id"] if a_score >= b_score else b["id"]
        remove_id = b["id"] if a_score >= b_score else a["id"]
        try:
            await merge_papers(keep_id, remove_id, db=db)
            merged += 1
        except Exception as e:
            logger.warning(f"Merge failed for {keep_id}/{remove_id}: {e}")
    return {"detected": len(result.get("duplicates", [])), "merged": merged}
