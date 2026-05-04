"""
Research Notebook API routes.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from backend.services.cluster_database import ClusterDatabaseService
from backend.api.routes.users import get_current_user, get_db
from backend.models.user import UserResponse
from backend.models.notebook import NotebookCreate, NotebookEntryCreate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", summary="Create a new notebook")
async def create_notebook(
    notebook_data: NotebookCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Create a new research notebook."""
    try:
        notebook = await db.create_notebook(
            user_id=current_user.id,
            title=notebook_data.title,
            description=notebook_data.description
        )
        return notebook
    except Exception as e:
        logger.error(f"Failed to create notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="List user notebooks")
async def list_notebooks(
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """List all notebooks for the current user."""
    try:
        notebooks = await db.get_user_notebooks(current_user.id)
        return notebooks
    except Exception as e:
        logger.error(f"Failed to list notebooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries", summary="Add entry to notebook")
async def add_notebook_entry(
    entry_data: NotebookEntryCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Add a new note, snippet, or draft to a notebook."""
    try:
        # Verify ownership of notebook
        # (Simplified: in production, check if current_user owns entry_data.notebook_id)
        
        entry = await db.create_notebook_entry(entry_data.model_dump())
        return entry
    except Exception as e:
        logger.error(f"Failed to add notebook entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notebook_id}/entries", summary="Get notebook entries")
async def get_notebook_entries(
    notebook_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get all entries for a specific notebook."""
    try:
        entries = await db.get_notebook_entries(notebook_id)
        return entries
    except Exception as e:
        logger.error(f"Failed to get entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
