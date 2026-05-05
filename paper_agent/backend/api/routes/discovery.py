"""
Research Discovery & Knowledge Distillery API routes.
"""

import logging
from typing import List, Optional

from backend.api.routes.users import get_current_user, get_db
from backend.models.user import UserResponse
from backend.services.analyzer import SemanticDistillery
from backend.services.cluster_database import ClusterDatabaseService
from fastapi import APIRouter, Body, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/contradictions", summary="Find contradictions across papers")
async def find_contradictions(
    doc_ids: List[str] = Body(...),
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Analyze multiple papers to find conflicting findings."""
    distillery = SemanticDistillery(db)
    try:
        results = await distillery.find_contradictions(doc_ids)
        return results
    except Exception as e:
        logger.error(f"Contradiction detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gaps", summary="Identify research gaps and hypotheses")
async def find_gaps(
    doc_ids: List[str] = Body(...),
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Perform gap analysis and generate new research hypotheses."""
    distillery = SemanticDistillery(db)
    try:
        results = await distillery.generate_research_gaps(doc_ids)
        return results
    except Exception as e:
        logger.error(f"Gap analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threads", summary="Start a new research thread")
async def start_thread(
    goal: str = Body(..., embed=True),
    doc_ids: List[str] = Body(..., embed=True),
    notebook_id: Optional[str] = Body(None, embed=True),
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Start a persisted AI-driven research session."""
    try:
        thread = await db.create_research_thread(
            user_id=current_user.id,
            goal=goal,
            docs=doc_ids,
            notebook_id=notebook_id
        )
        return thread
    except Exception as e:
        logger.error(f"Failed to start thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))
