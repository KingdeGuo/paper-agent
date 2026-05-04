"""AI-powered tag suggestions and smart tagging."""

import uuid
import json
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/suggest/{document_id}", summary="AI-suggest tags for a paper")
async def suggest_tags(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """AI-suggest relevant tags/keywords for a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Document not found"}

    text = f"Title: {doc.title}\nAuthors: {', '.join(doc.authors or [])}\nYear: {doc.year}\nAbstract: {(doc.abstract or '')[:1000]}"

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Suggest 5-10 relevant tags/keywords for this academic paper. Output as JSON array of strings. Be specific and use standard academic terminology.\n\n{text}"}],
            system_prompt="You are an academic paper tagging system. Output valid JSON only.",
        )
        content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\[.*?\]', content, re.DOTALL)
        tags = json.loads(match.group()) if match else []
    except Exception:
        tags = ["machine-learning", "artificial-intelligence"]

    return {"document_id": document_id, "suggested_tags": tags[:10]}


@router.put("/apply/{document_id}", summary="Apply tags to a paper")
async def apply_tags(document_id: str, tags: List[str], db=Depends(get_db)):
    """Apply tags to a paper (stored in doc_metadata)."""
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Document not found"}
    meta = doc.doc_metadata or {}
    meta["tags"] = tags
    await db.update_document(document_id, {"doc_metadata": meta, "keywords": tags})
    return {"document_id": document_id, "tags": tags}


@router.get("/all", summary="Get all tags across library")
async def get_all_tags(db=Depends(get_db)):
    """Get all unique tags across the library with counts."""
    docs = await db.get_documents(limit=200)
    tag_counts = {}
    for d in docs:
        for kw in (d.keywords or []):
            tag_counts[kw] = tag_counts.get(kw, 0) + 1
        meta_tags = (d.doc_metadata or {}).get("tags", [])
        for t in meta_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    return {"tags": [{"tag": t, "count": c} for t, c in sorted_tags], "total": len(sorted_tags)}


@router.get("/by-tag/{tag}", summary="Get papers by tag")
async def get_papers_by_tag(tag: str, db=Depends(get_db)):
    """Get all papers with a specific tag."""
    docs = await db.get_documents(limit=100)
    matched = []
    for d in docs:
        keywords = [k.lower() for k in (d.keywords or [])]
        meta_tags = [t.lower() for t in ((d.doc_metadata or {}).get("tags", []))]
        if tag.lower() in keywords or tag.lower() in meta_tags:
            matched.append({"id": d.id, "title": d.title or d.filename, "year": d.year,
                           "authors": d.authors or []})
    return {"tag": tag, "count": len(matched), "papers": matched}
