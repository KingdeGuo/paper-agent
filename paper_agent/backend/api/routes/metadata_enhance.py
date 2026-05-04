"""Metadata Auto-Enhancement — fix incomplete paper metadata using external APIs."""

import logging
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/metadata/enhance/{document_id}", summary="Enhance paper metadata")
async def enhance_metadata(document_id: str, db=Depends(get_db)):
    """Use external APIs to fill in missing metadata for a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    enhancements = {}
    original = {
        "title": doc.title,
        "authors": doc.authors or [],
        "year": doc.year,
        "abstract": doc.abstract,
    }

    # 1. Try DOI lookup
    meta = doc.doc_metadata or {}
    doi = meta.get("doi") or getattr(doc, "arxiv_id", None)
    if not doi and doc.title:
        # Search CrossRef by title
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("https://api.crossref.org/works",
                                         params={"query.title": doc.title, "rows": 1})
                if resp.status_code == 200:
                    items = resp.json().get("message", {}).get("items", [])
                    if items:
                        item = items[0]
                        doi = item.get("DOI")
                        if doi:
                            enhancements["doi"] = doi
                            meta["doi"] = doi

                            if not doc.authors:
                                authors = []
                                for a in item.get("author", []):
                                    given = a.get("given", "")
                                    family = a.get("family", "")
                                    if family:
                                        authors.append(f"{family}, {given}" if given else family)
                                if authors:
                                    enhancements["authors"] = authors

                            if not doc.year:
                                year = item.get("published-print", {}).get("date-parts", [[None]])[0][0] or \
                                       item.get("created", {}).get("date-parts", [[None]])[0][0]
                                if year:
                                    enhancements["year"] = int(year)

                            if not doc.abstract:
                                abstract = item.get("abstract", "")
                                if abstract:
                                    enhancements["abstract"] = abstract

                            journal = item.get("container-title", [""])[0] if item.get("container-title") else None
                            if journal:
                                meta["journal"] = journal
                            if item.get("volume"):
                                meta["volume"] = item["volume"]
                            if item.get("issue"):
                                meta["number"] = item["issue"]
                            if item.get("page"):
                                meta["pages"] = item["page"]
        except Exception as e:
            logger.warning(f"CrossRef lookup failed: {e}")

    # 2. Try arXiv if we have arxiv_id
    arxiv_id = getattr(doc, "arxiv_id", None) or meta.get("arxiv_id")
    if arxiv_id and not doc.abstract:
        try:
            from paper_agent.backend.services.arxiv_service import arxiv_service
            if arxiv_service:
                paper = arxiv_service.fetch_by_id(arxiv_id)
                if paper:
                    if not doc.abstract and paper.get("abstract"):
                        enhancements["abstract"] = paper["abstract"]
                    if not doc.authors and paper.get("authors"):
                        enhancements["authors"] = paper["authors"]
        except Exception as e:
            logger.warning(f"arXiv lookup failed: {e}")

    # Apply enhancements
    if enhancements:
        update_data = {}
        for key, value in enhancements.items():
            if key == "doi":
                continue
            update_data[key] = value

        if enhancements.get("doi") or meta != (doc.doc_metadata or {}):
            update_data["doc_metadata"] = meta

        if update_data:
            await db.update_document(document_id, update_data)
            logger.info(f"Enhanced metadata for {document_id}: {list(enhancements.keys())}")

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "enhancements_applied": list(enhancements.keys()),
        "enhanced_fields": enhancements,
        "had_missing_fields": sum(1 for v in original.values() if not v),
    }


@router.post("/metadata/enhance-all", summary="Enhance metadata for all papers")
async def enhance_all_metadata(db=Depends(get_db)):
    """Run metadata enhancement for all papers that have missing fields."""
    docs = await db.get_documents(limit=100) if db else []
    results = []
    for doc in docs:
        has_missing = not all([doc.title, doc.authors, doc.year, doc.abstract])
        if has_missing:
            try:
                result = await enhance_metadata(doc.id, db=db)
                results.append(result)
            except Exception as e:
                logger.warning(f"Enhancement failed for {doc.id}: {e}")

    return {
        "total_docs": len(docs),
        "enhanced": len(results),
        "results": results[:20],
    }
