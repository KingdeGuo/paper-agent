"""
Zotero integration API routes.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from backend.services.cluster_database import ClusterDatabaseService
from backend.api.routes.users import get_current_user, get_db
from backend.models.user import UserResponse
from backend.services.zotero_service import zotero_service
from backend.models.notebook import ZoteroConnectRequest

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/connect", summary="Connect Zotero account")
async def connect_zotero(
    creds: ZoteroConnectRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Save Zotero API credentials for the current user."""
    try:
        from paper_agent.backend.models.notebook import ZoteroCredential
        async with db.async_session_maker() as session:
            # Upsert credential
            from sqlalchemy import select
            result = await session.execute(
                select(ZoteroCredential).where(ZoteroCredential.user_id == current_user.id)
            )
            entry = result.scalar_one_or_none()
            
            if entry:
                entry.zotero_user_id = creds.zotero_user_id
                entry.api_key = creds.api_key
                entry.is_active = True
            else:
                entry = ZoteroCredential(
                    user_id=current_user.id,
                    zotero_user_id=creds.zotero_user_id,
                    api_key=creds.api_key
                )
                session.add(entry)
            
            await session.commit()
            return {"message": "Zotero connected successfully"}
    except Exception as e:
        logger.error(f"Failed to connect Zotero: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections", summary="List Zotero collections")
async def list_collections(
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Fetch collections from Zotero."""
    from paper_agent.backend.models.notebook import ZoteroCredential
    async with db.async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ZoteroCredential).where(ZoteroCredential.user_id == current_user.id)
        )
        creds = result.scalar_one_or_none()
        
        if not creds or not creds.is_active:
            raise HTTPException(status_code=400, detail="Zotero not connected")
        
        collections = await zotero_service.get_collections(creds.zotero_user_id, creds.api_key)
        return collections

@router.post("/import/{item_key}", summary="Import a Zotero item")
async def import_zotero_item(
    item_key: str,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Import a specific paper from Zotero to Paper Agent."""
    from paper_agent.backend.models.notebook import ZoteroCredential
    async with db.async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ZoteroCredential).where(ZoteroCredential.user_id == current_user.id)
        )
        creds = result.scalar_one_or_none()
        
        if not creds or not creds.is_active:
            raise HTTPException(status_code=400, detail="Zotero not connected")
        
        doc = await zotero_service.import_item(
            current_user.id, creds.zotero_user_id, creds.api_key, item_key, db
        )
        
        if not doc:
            raise HTTPException(status_code=500, detail="Failed to import item")
            
        return doc
