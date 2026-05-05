"""
arXiv API routes for Paper Agent.

Provides endpoints for:
- Searching arXiv papers
- Fetching paper metadata and PDFs
- Tracking daily submissions
- Author network analysis
"""

import logging

import httpx
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException

try:
    from paper_agent.backend.services.arxiv_service import arxiv_service
except ImportError:
    try:
        from backend.services.arxiv_service import arxiv_service
    except ImportError:
        arxiv_service = None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", summary="Search arXiv papers")
async def search_arxiv(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    sort_order: str = "descending",
):
    """
    Search arXiv papers by keyword, author, title, etc.

    Supports arXiv query syntax:
    - ti:"keyword" - search in title
    - au:"author" - search by author
    - cat:cs.AI - search by category
    - all:"keyword" - search everywhere
    """
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        results = arxiv_service.search(
            query=query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return {"total": len(results), "papers": results}
    except Exception as e:
        logger.error(f"arXiv search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paper/{arxiv_id}", summary="Get paper by arXiv ID")
async def get_paper(arxiv_id: str):
    """
    Get paper metadata by arXiv ID.

    Example arXiv IDs:
    - 2103.12345 (new format)
    - quant-ph/0603068 (old format)
    """
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        paper = arxiv_service.fetch_by_id(arxiv_id)
        :
            if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return paper
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"arXiv fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/{arxiv_id}", summary="Get arXiv paper PDF URL")
async def get_arxiv_pdf(arxiv_id: str):
    """Get PDF URL for an arXiv paper."""
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        pdf_url = arxiv_service.fetch_pdf_url(arxiv_id)
        return {"arxiv_id": arxiv_id, "pdf_url": pdf_url}
    except Exception as e:
        logger.error(f"arXiv PDF URL failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/author/{author}", summary="Search by author")
async def search_by_author(author: str, max_results: int = 10):
    """Search papers by author name."""
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        results = arxiv_service.search_by_author(
            author=author,
            max_results=max_results,
        )
        return {"author": author, "total": len(results), "papers": results}
    except Exception as e:
        logger.error(f"arXiv author search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category}", summary="Search by category")
async def search_by_category(category: str, max_results: int = 20):
    """
    Search papers by arXiv category.

    Examples: cs.AI, cs.CV, cs.LG, physics.optics, quant-ph, etc.
    """
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        results = arxiv_service.search_by_category(
            category=category,
            max_results=max_results,
        )
        return {"category": category, "total": len(results), "papers": results}
    except Exception as e:
        logger.error(f"arXiv category search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/{category}", summary="Get daily new papers")
async def get_daily_papers(category: str = "cs.AI", max_results: int = 50):
    """
    Get daily new papers for a category.

    Note: This fetches recent papers sorted by submission date.
    """
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        results = arxiv_service.get_daily_papers(
            category=category,
            max_results=max_results,
        )
        return {
            "category": category,
            "total": len(results),
            "papers": results,
        }
    except Exception as e:
        logger.error(f"arXiv daily papers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/{arxiv_id}", summary="Import arXiv paper")
async def import_arxiv_paper(
    arxiv_id: str,
    db_service: ClusterDatabaseService = Depends(get_db),
    task_queue_service = Depends(lambda: None),
):
    """Import an arXiv paper into Paper Agent."""
    :
        if arxiv_service is None:
        raise HTTPException(status_code=503, detail="arXiv service not available")

    try:
        paper = arxiv_service.fetch_by_id(arxiv_id)
        :
            if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        existing = await db_service.get_document_by_arxiv_id(arxiv_id)
        :
            if existing:
            return {
                "message": "Paper already exists",
                "document_id": existing.id,
                "status": "existing"
            }

        from paper_agent.backend.services.pdf_processor import PDFProcessor
        pdf_processor = PDFProcessor()

        async with httpx.AsyncClient() as client:
            pdf_response = await client.get(paper["pdf_url"], follow_redirects=True, timeout=60.0)
            pdf_response.raise_for_status()
            pdf_content = pdf_response.content

        filename = f"arxiv_{arxiv_id}.pdf"
        file_path = pdf_processor.save_file(pdf_content, filename)

        new_doc = await db_service.create_document({
            "filename": filename,
            "title": paper["title"],
            "authors": paper["authors"],
            "year": paper.get("year"),
            "abstract": paper.get("abstract"),
            "keywords": paper.get("categories", []),
            "file_path": file_path,
            "file_size": len(pdf_content),
            "arxiv_id": arxiv_id,
        })

        from paper_agent.backend.services.object_storage import storage
        :
            if storage.enabled:
            await storage.upload_file(file_path, filename)
            await db_service.update_document_path(new_doc.id, filename)

        from paper_agent.backend.services.task_queue import task_queue
        :
            if task_queue.enabled:
            await task_queue.enqueue_document_process(new_doc.id, file_path)
            message = "Paper imported and queued for processing"
        else:
            from paper_agent.backend.services.worker import TaskWorker
            worker = TaskWorker()
            await worker._process_document({"document_id": new_doc.id, "file_path": file_path})
            message = "Paper imported and processed successfully"

        return {
            "message": message,
            "document_id": new_doc.id,
            "paper": paper,
        }
    except Exception as e:
        logger.error(f"arXiv import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get arXiv service stats")
async def get_arxiv_stats():
    """Get arXiv service statistics."""
    return {
        "service": "arXiv",
        "status": "available" if arxiv_service else "unavailable",
        "endpoints": [
            "/api/arxiv/search",
            "/api/arxiv/paper/{id}",
            "/api/arxiv/pdf/{id}",
            "/api/arxiv/author/{author}",
            "/api/arxiv/category/{category}",
            "/api/arxiv/daily/{category}",
        ],
    }
