"""Citation Chain Explorer — follow citations forward and backward."""

import json
import logging
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/citation-chain/{document_id}", summary="Explore citation chain")
async def explore_citation_chain(document_id: str, direction: str = "both",
                                  depth: int = 1, db=Depends(get_db)):
    """Explore citation chains: find papers that cite or are cited by this paper."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = {
        "center_paper": {
            "id": doc.id,
            "title": doc.title or doc.filename,
            "authors": doc.authors or [],
            "year": doc.year,
            "abstract": (doc.abstract or "")[:300],
        },
        "citations": [],
        "cited_by": [],
        "total_count": 0,
    }

    # 1. Find backward citations (papers referenced by this paper)
    # Use Semantic Scholar API
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Get paper details from Semantic Scholar by title search
            title_query = doc.title or doc.filename
            if title_query:
                resp = await client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={"query": title_query, "limit": 3},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    papers = data.get("data", [])
                    if papers:
                        paper_id = papers[0].get("paperId")
                        if paper_id:
                            # Get citations
                            cit_resp = await client.get(
                                f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations",
                                params={"limit": 20},
                            )
                            if cit_resp.status_code == 200:
                                cit_data = cit_resp.json()
                                for c in cit_data.get("data", [])[:10]:
                                    cp = c.get("citingPaper", {})
                                    result["citations"].append({
                                        "title": cp.get("title", "Unknown"),
                                        "year": cp.get("year"),
                                        "authors": [a.get("name", "") for a in cp.get("authors", [])[:3]],
                                        "url": f"https://www.semanticscholar.org/paper/{cp.get('paperId', '')}",
                                        "direction": "references" if direction in ("both", "backward") else None,
                                    })

                            # Get references
                            ref_resp = await client.get(
                                f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references",
                                params={"limit": 20},
                            )
                            if ref_resp.status_code == 200:
                                ref_data = ref_resp.json()
                                for r in ref_data.get("data", [])[:10]:
                                    rp = r.get("citedPaper", {})
                                    result["cited_by"].append({
                                        "title": rp.get("title", "Unknown"),
                                        "year": rp.get("year"),
                                        "authors": [a.get("name", "") for a in rp.get("authors", [])[:3]],
                                        "url": f"https://www.semanticscholar.org/paper/{rp.get('paperId', '')}",
                                        "direction": "cited_by" if direction in ("both", "forward") else None,
                                    })
    except Exception as e:
        logger.warning(f"Semantic Scholar lookup failed: {e}")

    result["total_count"] = len(result["citations"]) + len(result["cited_by"])

    # 2. Check which of these papers are already in the user's library
    all_titles = set()
    for p in result["citations"] + result["cited_by"]:
        if p.get("title"):
            all_titles.add(p["title"].lower())

    library_docs = await db.get_documents(limit=100) if db else []
    in_library = set()
    for ld in library_docs:
        lt = (ld.title or "").lower()
        if lt in all_titles:
            in_library.add(lt)

    for p in result["citations"] + result["cited_by"]:
        p["in_library"] = (p.get("title", "").lower() in in_library)

    return result


@router.get("/citation-chain/suggest/{document_id}", summary="Suggest papers to add")
async def suggest_papers_from_chain(document_id: str, db=Depends(get_db)):
    """Suggest papers from the citation chain that aren't in the library yet."""
    chain = await explore_citation_chain(document_id, depth=1, db=db)
    suggestions = []
    for p in chain.get("citations", []) + chain.get("cited_by", []):
        if not p.get("in_library") and p.get("title") and p.get("title") != "Unknown":
            # Check if we can get more info
            suggestions.append({
                "title": p["title"],
                "year": p.get("year"),
                "authors": p.get("authors", []),
                "url": p.get("url", ""),
                "reason": f"Cited by or references '{chain['center_paper']['title']}'",
            })
    return {
        "center_paper": chain["center_paper"],
        "suggestions": suggestions[:15],
        "count": len(suggestions[:15]),
    }
