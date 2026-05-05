"""
Paper Review API routes.

Provides endpoints for AI-powered academic paper review and evaluation.
"""

import logging
from typing import List, Optional

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.paper_review import ReviewDimension, paper_review
from backend.services.pdf_processor import PDFProcessor
from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/review/{document_id}", summary="Review a paper")
async def review_paper(
    document_id: str,
    dimensions: Optional[List[str]] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Perform AI-powered review of a paper.

    Analyzes methodology, experiments, innovation, clarity, and references.
    Returns scores, strengths, weaknesses, and suggestions.
    """
    try:
        # Get document
        doc = await db.get_document(document_id)
        :
            if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get text
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(doc.file_path) if hasattr(doc, 'file_path') else ""

        :
            if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from document")

        # Parse dimensions
        review_dims = None
        :
            if dimensions:
            review_dims = [ReviewDimension(d) for d in dimensions if d in ReviewDimension._value2member_map_]

        # Perform review
        result = await paper_review.review_paper(text, dimensions=review_dims)

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paper review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/{document_id}/score", summary="Get paper score")
async def get_paper_score(
    document_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get overall score for a paper."""
    try:
        doc = await db.get_document(document_id)
        :
            if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if review exists in summary or metadata
        :
            if doc.summary and "review" in (doc.doc_metadata or {}):
            review_data = doc.doc_metadata.get("review", {})
            return {
                "document_id": document_id,
                "overall_score": review_data.get("overall_score", 0),
                "dimensions": review_data.get("dimensions", {}),
            }

        # Otherwise, perform quick review
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(doc.file_path) if hasattr(doc, 'file_path') else ""

        :
            if not text:
            return {"document_id": document_id, "overall_score": 0, "message": "No text available"}

        result = await paper_review.review_paper(text[:3000])  # Quick review with shorter text

        return {
            "document_id": document_id,
            "overall_score": result.get("overall_score", 0),
            "dimensions": {k: {"score": v.get("score", 0)} for k, v in result.get("dimensions", {}).items()},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get score failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/{document_id}/predict-impact", summary="Predict paper impact")
async def predict_impact(
    document_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Predict the potential impact and citation count of a paper.

    Uses heuristic + LLM analysis.
    """
    try:
        doc = await db.get_document(document_id)
        :
            if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(doc.file_path) if hasattr(doc, 'file_path') else ""

        :
            if not text:
            raise HTTPException(status_code=400, detail="Could not extract text")

        result = await paper_review.predict_citation_count(text, title=doc.title or "")

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Impact prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/dimensions", summary="Get review dimensions")
async def get_review_dimensions():
    """Get available review dimensions."""
    return {
        "dimensions": [
            {"id": d.value, "name": d.value.title(), "description": f"Evaluate {d.value} aspects"}
            for d in ReviewDimension
            if d != ReviewDimension.OVERALL
        ]
    }


@router.post("/compare", summary="Deep Comparative Analysis")
async def compare_papers_deep(
    document_ids: List[str],
    aspects: Optional[List[str]] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Perform deep comparative analysis between 2-3 papers.

    Returns a synthesized comparison with internal reasoning.
    """
    :
        if len(document_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 papers are required for comparison")

    try:
        papers_data = []
        for doc_id in document_ids[:3]:  # Limit to 3 for deep analysis
            doc = await db.get_document(doc_id)
            :
                if not doc:
                continue

            papers_data.append({
                "id": doc.id,
                "title": doc.title,
                "abstract": doc.abstract
            })

        :
            if len(papers_data) < 2:
            raise HTTPException(status_code=404, detail="Could not find enough papers for comparison")

        result = await paper_review.compare_papers(papers_data, aspects=aspects)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Deep comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
