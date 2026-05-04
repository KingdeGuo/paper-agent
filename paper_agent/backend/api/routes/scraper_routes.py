"""AI Academic Scraper API — extract paper metadata from any URL."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query

from backend.services.academic_scraper import scraper, AcademicScraper
from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/scrape", summary="Extract paper metadata from URL")
async def extract_paper(url: str, use_llm: bool = True):
    """Extract paper metadata from any academic URL using AI."""
    result = await scraper.extract(url, use_llm=use_llm)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/scrape/batch", summary="Extract from multiple URLs")
async def batch_extract(urls: List[str]):
    """Extract paper metadata from multiple URLs at once."""
    results = await scraper.batch_extract(urls)
    return {
        "total": len(results),
        "successful": sum(1 for r in results if "error" not in r),
        "results": results,
    }


@router.post("/scrape/import", summary="Scrape and import paper")
async def scrape_and_import(url: str, db=Depends(get_db)):
    """Extract metadata from a URL and import the paper into your library."""
    result = await scraper.extract(url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    pdf_url = await scraper.find_pdf_url(url)
    pdf_content = None
    file_path = ""

    # Download PDF if available
    if pdf_url:
        try:
            client = await scraper._get_client()
            pdf_resp = await client.get(pdf_url)
            if pdf_resp.status_code == 200 and "application/pdf" in pdf_resp.headers.get("content-type", ""):
                pdf_content = pdf_resp.content
                import os
                os.makedirs("data/pdfs", exist_ok=True)
                filename = f"imported_{result.get('arxiv_id') or result.get('doi', 'paper').replace('/', '_')}.pdf"
                file_path = f"data/pdfs/{filename}"
                with open(file_path, "wb") as f:
                    f.write(pdf_content)
        except Exception as e:
            logger.warning(f"PDF download failed: {e}")

    # Create document
    doc = await db.create_document({
        "filename": file_path.split("/")[-1] if file_path else f"imported_{result.get('doi', 'unknown')}.pdf",
        "title": result.get("title", "Untitled"),
        "authors": result.get("authors", []),
        "year": result.get("year"),
        "abstract": result.get("abstract", ""),
        "keywords": result.get("keywords", []),
        "file_path": file_path,
        "file_size": len(pdf_content) if pdf_content else 0,
        "processed": 0,
        "doc_metadata": {
            "doi": result.get("doi"),
            "journal": result.get("journal") or result.get("venue"),
            "arxiv_id": result.get("arxiv_id"),
            "source_url": url,
            "pdf_url": pdf_url,
            "confidence": result.get("confidence"),
        },
    })

    return {
        "document_id": doc.id,
        "title": doc.title,
        "metadata": result,
        "pdf_downloaded": pdf_content is not None,
    }


@router.get("/scrape/sources", summary="List supported sources")
async def list_sources():
    """List all supported academic sources for extraction."""
    from backend.services.academic_scraper import SITE_EXTRACTORS
    return {
        "site_specific": list(SITE_EXTRACTORS.keys()),
        "meta_tag_support": "All sites with citation meta tags (most publishers)",
        "llm_fallback": "Any URL (using LLM extraction)",
        "total_supported": len(SITE_EXTRACTORS) + 2,
    }
