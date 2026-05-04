"""
API routes for Drafting and Research Mentoring.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from backend.services.cluster_database import ClusterDatabaseService
from backend.api.routes.users import get_current_user, get_db
from backend.models.user import UserResponse
from backend.services.drafting_service import DraftingService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate services (in real app, use registry)
llm_service = LLMService()

@router.post("/related-work", summary="Generate a LaTeX Related Work section")
async def generate_related_work(
    doc_ids: List[str] = Body(..., embed=True),
    focus_topic: str = Body(..., embed=True),
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Analyze selected papers and draft a LaTeX-formatted literature review."""
    drafter = DraftingService(db, llm_service)
    try:
        result = await drafter.generate_related_work(doc_ids, focus_topic)
        return result
    except Exception as e:
        logger.error(f"Drafting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decode-formula", summary="Explain mathematical formula")
async def decode_formula(
    formula: str = Body(..., embed=True),
    context: str = Body("", embed=True),
    current_user: UserResponse = Depends(get_current_user),
):
    """Explain a complex LaTeX formula in plain scientific language."""
    drafter = DraftingService(None, llm_service)
    try:
        result = await drafter.decode_formula(formula, context)
        return result
    except Exception as e:
        logger.error(f"Formula decoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/grounded-chat", summary="Grounded QA with citations")
async def grounded_chat(
    question: str = Body(..., embed=True),
    doc_ids: List[str] = Body(..., embed=True),
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Chat with AI about papers with mandatory source grounding."""
    docs_context = []
    for d_id in doc_ids:
        doc = await db.get_document(d_id)
        if doc:
            # Fetch some relevant snippets (simplified: use abstract and summary)
            docs_context.append({
                "id": doc.id,
                "title": doc.title,
                "snippets": f"Abstract: {doc.abstract}\nSummary: {doc.summary}"
            })
    
    try:
        result = await llm_service.chat_with_grounding(
            messages=[{"role": "user", "content": question}],
            context_docs=docs_context
        )
        return result
    except Exception as e:
        logger.error(f"Grounded chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
