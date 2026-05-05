"""Multi-Source Search — search arXiv, PubMed, CrossRef, and local library simultaneously."""

import logging

import httpx
from backend.services.registry import get_db, get_vector_service
from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/multi-search", summary="Search multiple sources at once")
async def multi_source_search(
    query: str = Query(...),
    sources: str = Query("arxiv,pubmed,crossref,local"),
    limit: int = Query(default=5, le=20),
    db=Depends(get_db),
    vector_service=Depends(get_vector_service),
):
    """Search across arXiv, PubMed, CrossRef, and your local library simultaneously."""
    source_list = [s.strip() for s in sources.split(",")]
    results = {}
    errors = []

    tasks = []

    # Local search
    if "local" in source_list:
        try:
            if vector_service:
                local_results = vector_service.search_similar(query, limit=limit)
            else:
                local_results = await db.search_documents(query, limit=limit) if db else []

            enriched = []
            for r in local_results:
                if isinstance(r, dict):
                    did = r.get("document_id", r.get("id", ""))
                    doc = await db.get_document(did) if did else None
                    enriched.append({
                        "title": r.get("title") or (doc.title if doc else "Untitled"),
                        "authors": r.get("authors") or (doc.authors if doc else []),
                        "year": r.get("year") or (doc.year if doc else None),
                        "source": "local",
                        "id": did,
                        "score": r.get("score", 0),
                        "snippet": r.get("text", "")[:200] if r.get("text") else (doc.abstract or "")[:200] if doc else "",
                    })
                else:
                    enriched.append({
                        "title": r.title or r.filename,
                        "authors": r.authors or [],
                        "year": r.year,
                        "source": "local",
                        "id": r.id,
                        "score": 1.0,
                        "snippet": (r.abstract or "")[:200],
                    })
            results["local"] = enriched[:limit]
        except Exception as e:
            errors.append(f"local: {e}")
            results["local"] = []

    # arXiv search
    if "arxiv" in source_list:
        try:
            from paper_agent.backend.services.arxiv_service import arxiv_service
            if arxiv_service:
                arxiv_results = arxiv_service.search(query, max_results=limit)
                results["arxiv"] = [{
                    "title": p.get("title", "Untitled"),
                    "authors": p.get("authors", []),
                    "year": p.get("year"),
                    "source": "arxiv",
                    "id": p.get("arxiv_id", ""),
                    "url": f"https://arxiv.org/abs/{p.get('arxiv_id', '')}",
                    "snippet": (p.get("abstract", "") or "")[:200],
                } for p in (arxiv_results or [])[:limit]]
            else:
                results["arxiv"] = []
        except Exception as e:
            errors.append(f"arxiv: {e}")
            results["arxiv"] = []

    # PubMed search
    if "pubmed" in source_list:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                esearch = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                                           params={"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"})
                if esearch.status_code == 200:
                    id_list = esearch.json().get("esearchresult", {}).get("idlist", [])
                    pubmed_results = []
                    for pmid in id_list[:limit]:
                        esummary = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                                                     params={"db": "pubmed", "id": pmid, "retmode": "json"})
                        if esummary.status_code == 200:
                            data = esummary.json().get("result", {}).get(pmid, {})
                            pubmed_results.append({
                                "title": data.get("title", "Untitled"),
                                "authors": [a.get("name", "") for a in data.get("authors", [])[:5]],
                                "year": data.get("pubdate", "")[:4] if data.get("pubdate") else None,
                                "source": "pubmed",
                                "id": pmid,
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                "snippet": (data.get("source", "") or ""),
                            })
                    results["pubmed"] = pubmed_results
                else:
                    results["pubmed"] = []
        except Exception as e:
            errors.append(f"pubmed: {e}")
            results["pubmed"] = []

    # CrossRef search
    if "crossref" in source_list:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                cr_resp = await client.get("https://api.crossref.org/works",
                                           params={"query": query, "rows": limit})
                if cr_resp.status_code == 200:
                    items = cr_resp.json().get("message", {}).get("items", [])
                    results["crossref"] = [{
                        "title": item.get("title", ["Untitled"])[0] if item.get("title") else "Untitled",
                        "authors": [f"{a.get('family', '')} {a.get('given', '')}".strip() for a in item.get("author", [])[:5]],
                        "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                                item.get("created", {}).get("date-parts", [[None]])[0][0],
                        "source": "crossref",
                        "id": item.get("DOI", ""),
                        "url": f"https://doi.org/{item.get('DOI', '')}",
                        "snippet": "",
                    } for item in items[:limit]]
                else:
                    results["crossref"] = []
        except Exception as e:
            errors.append(f"crossref: {e}")
            results["crossref"] = []

    # Combine and rank
    all_results = []
    for source, items in results.items():
        for item in items:
            all_results.append(item)

    all_results.sort(key=lambda x: -x.get("score", 0) if x.get("score") else 0)

    return {
        "query": query,
        "sources_searched": source_list,
        "total_results": len(all_results),
        "by_source": {s: len(results.get(s, [])) for s in source_list},
        "results": all_results[:limit * 4],
        "errors": errors if errors else None,
    }
