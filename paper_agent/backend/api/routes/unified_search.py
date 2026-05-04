"""Unified Smart Search — one search bar for everything (papers, discussions, codex, glossary, tags)."""

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_vector_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.vector_service import VectorService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search-unified", summary="Search everything")
async def unified_search(
    query: str = Query(...),
    limit: int = Query(default=20, le=50),
    sources: str = Query(default="papers,discussions,codex,glossary,tags"),
    db=Depends(get_db),
    vector_service=Depends(get_vector_service),
):
    """Search across all subsystems simultaneously."""
    source_list = [s.strip() for s in sources.split(",")]
    results = {}
    meta = {"total": 0}

    # 1. Papers (using vector search)
    if "papers" in source_list:
        try:
            vec_results = []
            if vector_service:
                vec_results = vector_service.search_similar(query, limit=limit)
            local_results = []
            try:
                local_results = await db.search_documents(query, limit=limit) if db else []
            except: pass

            papers = []
            seen_ids = set()
            for r in vec_results:
                did = r.get("document_id", r.get("id", ""))
                if did and did not in seen_ids:
                    seen_ids.add(did)
                    doc = await db.get_document(did) if did else None
                    papers.append({
                        "type": "paper",
                        "id": did,
                        "title": r.get("title") or (doc.title if doc else "Untitled"),
                        "snippet": r.get("text", "")[:200],
                        "score": r.get("score", 0),
                        "authors": (doc.authors if doc else []) or [],
                        "year": doc.year if doc else None,
                    })

            for r in local_results:
                if r.id not in seen_ids and len(papers) < limit:
                    papers.append({
                        "type": "paper", "id": r.id,
                        "title": r.title or r.filename,
                        "snippet": (r.abstract or "")[:200],
                        "score": 0.5, "authors": r.authors or [],
                        "year": r.year,
                    })

            papers.sort(key=lambda x: -x["score"])
            results["papers"] = papers[:limit]
            meta["paper_count"] = len(papers)
        except Exception as e:
            results["papers"] = []
            meta["paper_error"] = str(e)

    # 2. Discussions
    if "discussions" in source_list:
        try:
            async with db.async_session_maker() as session:
                rows = (await session.execute(sa_text(
                    "SELECT pd.id, pd.title, pd.content, pd.discussion_type, pd.document_id, d.title as doc_title "
                    "FROM paper_discussions pd LEFT JOIN documents d ON pd.document_id = d.id "
                    "WHERE pd.is_deleted = 0 AND (pd.title LIKE :q OR pd.content LIKE :q) "
                    "ORDER BY pd.upvotes DESC LIMIT :lim"),
                    {"q": f"%{query}%", "lim": limit})).fetchall()
                results["discussions"] = [{
                    "type": "discussion", "id": r[0],
                    "title": r[1] or r[2][:50], "snippet": (r[2] or "")[:200],
                    "discussion_type": r[3], "document_id": r[4],
                    "document_title": r[5], "score": 0.8,
                } for r in rows]
                meta["discussion_count"] = len(rows)
        except Exception as e:
            results["discussions"] = []
    else:
        results["discussions"] = []

    # 3. Codex entries
    if "codex" in source_list:
        try:
            async with db.async_session_maker() as session:
                rows = (await session.execute(sa_text(
                    "SELECT id, title, content, entry_type, importance FROM codex_entries "
                    "WHERE user_id = 'default' AND is_deleted = 0 AND (title LIKE :q OR content LIKE :q) "
                    "ORDER BY importance DESC LIMIT :lim"),
                    {"q": f"%{query}%", "lim": limit})).fetchall()
                results["codex"] = [{
                    "type": "codex", "id": r[0],
                    "title": r[1], "snippet": (r[2] or "")[:200],
                    "entry_type": r[3], "importance": r[4] or 0,
                } for r in rows]
                meta["codex_count"] = len(rows)
        except Exception as e:
            results["codex"] = []
    else:
        results["codex"] = []

    # 4. Glossary
    if "glossary" in source_list:
        try:
            async with db.async_session_maker() as session:
                rows = (await session.execute(sa_text(
                    "SELECT id, term, definition, category FROM concept_glossary "
                    "WHERE user_id = 'default' AND (term LIKE :q OR definition LIKE :q) "
                    "ORDER BY term ASC LIMIT :lim"),
                    {"q": f"%{query}%", "lim": limit})).fetchall()
                results["glossary"] = [{
                    "type": "glossary", "id": r[0],
                    "title": r[1], "snippet": (r[2] or "")[:200],
                    "category": r[3] or "general",
                } for r in rows]
                meta["glossary_count"] = len(rows)
        except Exception as e:
            results["glossary"] = []
    else:
        results["glossary"] = []

    # 5. Tags
    if "tags" in source_list:
        try:
            docs = await db.get_documents(limit=100) if db else []
            matched_tags = []
            seen_tags = set()
            for d in docs:
                for kw in (d.keywords or []):
                    if query.lower() in kw.lower() and kw.lower() not in seen_tags:
                        seen_tags.add(kw.lower())
                        matched_tags.append({"type": "tag", "title": kw, "count": 1, "id": kw})
            results["tags"] = matched_tags[:limit]
            meta["tag_count"] = len(matched_tags)
        except Exception as e:
            results["tags"] = []
    else:
        results["tags"] = []

    # Combine all results
    all_results = []
    for category, items in results.items():
        for item in items:
            all_results.append(item)

    all_results.sort(key=lambda x: -x.get("score", 0.5))
    meta["total"] = len(all_results)
    meta["sources_searched"] = source_list

    return {"query": query, "results": all_results, "by_source": {k: len(v) for k, v in results.items()}, "meta": meta}
