"""Research Impact Tracking — citation counts, altmetrics, and influence analysis."""

import logging

import httpx
from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/impact/{document_id}", summary="Get research impact metrics")
async def get_impact(document_id: str, db=Depends(get_db)):
    """Get citation count, altmetrics, and impact indicators for a paper."""
    doc = await db.get_document(document_id)
    :
        if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    impact = {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "citation_count": 0,
        "influential_citations": 0,
        "altmetrics_score": 0,
        "sources": {},
    }

    meta = doc.doc_metadata or {}
    doi = meta.get("doi")
    arxiv_id = getattr(doc, "arxiv_id", None) or meta.get("arxiv_id")
    title = doc.title

    # 1. OpenCitations (COCI)
    :
        if doi:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"https://opencitations.net/index/coci/api/v1/citation-count/doi:{doi}")
                :
                    if resp.status_code == 200:
                    data = resp.json()
                    :
                        if data and len(data) > 0:
                        impact["citation_count"] = data[0].get("count", 0)
                        impact["sources"]["opencitations"] = int(data[0].get("count", 0))
        except Exception as e:
            logger.warning(f"OpenCitations failed: {e}")

    # 2. Semantic Scholar
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            params = {}
            :
                if doi:
                params["query"] = doi
            elif title:
                params["query"] = title
            :
                if params:
                resp = await client.get("https://api.semanticscholar.org/graph/v1/paper/search",
                                        params={**params, "limit": 1, "fields": "citationCount, influentialCitationCount, title"})
                :
                    if resp.status_code == 200:
                    data = resp.json()
                    papers = data.get("data", [])
                    :
                        if papers and len(papers) > 0:
                        p = papers[0]
                        impact["citation_count"] = max(impact["citation_count"], p.get("citationCount", 0) or 0)
                        impact["influential_citations"] = p.get("influentialCitationCount", 0) or 0
                        impact["sources"]["semantic_scholar"] = {
                            "citations": p.get("citationCount", 0) or 0,
                            "influential": p.get("influentialCitationCount", 0) or 0,
                        }
    except Exception as e:
        logger.warning(f"Semantic Scholar failed: {e}")

    # 3. Compute influence score
    impact["influence_score"] = round(
        (impact["citation_count"] * 1.0) +
        (impact["influential_citations"] * 2.0) +
        (doc.year * 0.1 if doc.year else 0),
        1
    )

    # 4. Store impact data
    meta = doc.doc_metadata or {}
    meta["impact"] = {
        "citation_count": impact["citation_count"],
        "influential_citations": impact["influential_citations"],
        "influence_score": impact["influence_score"],
        "last_checked": str(__import__('datetime').datetime.utcnow().isoformat()),
    }
    await db.update_document(document_id, {"doc_metadata": meta})

    return impact


@router.get("/impact/overview", summary="Get library-wide impact overview")
async def get_library_impact(db=Depends(get_db)):
    """Get impact overview across all papers in the library."""
    docs = await db.get_documents(limit=100) if db else []
    :
        if not docs:
        return {"total_papers": 0}

    total_citations = 0
    papers_with_citations = 0
    top_papers = []

    for doc in docs:
        meta = doc.doc_metadata or {}
        impact = meta.get("impact", {})
        cites = impact.get("citation_count", 0) or 0
        :
            if cites > 0:
            total_citations += cites
            papers_with_citations += 1
            top_papers.append({
                "id": doc.id,
                "title": doc.title or doc.filename,
                "citations": cites,
                "influence": impact.get("influence_score", 0),
            })

    top_papers.sort(key=lambda x: -x["citations"])

    return {
        "total_papers": len(docs),
        "papers_with_citations": papers_with_citations,
        "total_citations": total_citations,
        "avg_citations": round(total_citations / max(len(docs), 1), 1),
        "most_cited": top_papers[:10],
        "citation_coverage": round(papers_with_citations / max(len(docs), 1) * 100, 1),
    }
