"""Re-ranking pipeline API — two-stage search refinement."""

import logging

from backend.services.registry import get_db, get_vector_service
from backend.services.reranking_service import RerankingPipeline
from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/rerank", summary="Re-rank search results")
async def rerank_results(
    query: str = Query(...),
    top_k: int = 5,
    method: str = "hybrid",
    db=Depends(get_db),
    vector_service=Depends(get_vector_service),
):
    """Re-rank search results using cross-encoder style scoring."""
    # Get initial candidates
    candidates = []
    if vector_service:
        candidates = vector_service.search_similar(query, limit=20)
    if not candidates and db:
        docs = await db.search_documents(query, limit=20) if hasattr(db, 'search_documents') else []
        candidates = [{"document_id": d.id, "title": d.title, "text": d.abstract or ""} for d in docs]

    if not candidates:
        return {"query": query, "results": [], "count": 0}

    # Re-rank
    pipeline = RerankingPipeline()
    reranked = await pipeline.rerank(query, candidates, top_k, method=method)

    # Enrich with document details
    results = []
    for r in reranked:
        did = r.get("document_id")
        doc = await db.get_document(did) if db and did else None
        results.append({
            "document_id": did,
            "title": r.get("title") or (doc.title if doc else "Untitled"),
            "authors": doc.authors if doc else [],
            "year": doc.year if doc else None,
            "abstract": (doc.abstract or "")[:300] if doc else "",
            "relevance_score": r.get("relevance_score", 0),
            "rerank_method": method,
        })

    return {"query": query, "results": results, "count": len(results), "method": method}


@router.get("/rerank/stats", summary="Re-ranking statistics")
async def rerank_stats(db=Depends(get_db)):
    """Get re-ranking performance statistics."""
    return {
        "available_methods": ["keyword", "llm", "hybrid"],
        "recommended_method": "hybrid",
        "description": "Hybrid re-ranking combines keyword overlap (40%) with LLM relevance scoring (60%) for best results.",
        "supported": True,
    }
