"""
Annotation and notes API routes.

Supports:
- Text highlighting and annotation
- Notes and comments on PDF pages
- Bookmark management
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from backend.services.cluster_database import ClusterDatabaseService, Document
from backend.services.registry import get_db
from backend.models.annotation import (
    AnnotationCreate, AnnotationResponse, AnnotationUpdate,
    NoteCreate, NoteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{document_id}", summary="Get annotations for a document")
async def get_annotations(
    document_id: str,
    page: Optional[int] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Get all annotations/highlights for a document.
    
    Optionally filter by page number.
    """
    try:
        from sqlalchemy import select
        from backend.models.annotation import Annotation
        
        async with db.async_session_maker() as session:
            query = select(Annotation).where(
                Annotation.document_id == document_id,
                Annotation.is_deleted == False,
            )
            
            if page is not None:
                query = query.where(Annotation.page_number == page)
            
            result = await session.execute(query.order_by(Annotation.page_number, Annotation.created_at))
            annotations = result.scalars().all()
            
            return {
                "document_id": document_id,
                "annotations": [AnnotationResponse.model_validate(a).model_dump() for a in annotations],
                "count": len(annotations),
            }
            
    except Exception as e:
        logger.error(f"Get annotations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}", summary="Create annotation")
async def create_annotation(
    document_id: str,
    annotation: AnnotationCreate,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Create a new text highlight/annotation."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Annotation
        
        async with db.async_session_maker() as session:
            # Verify document exists
            doc_result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            if not doc_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Create annotation
            ann_id = str(uuid.uuid4())
            new_annotation = Annotation(
                id=ann_id,
                document_id=document_id,
                page_number=annotation.page_number,
                text=annotation.text,
                highlight_color=annotation.highlight_color or "#FFEB3B",
                note=annotation.note,
                position_x=annotation.position_x,
                position_y=annotation.position_y,
                width=annotation.width,
                height=annotation.height,
            )
            
            session.add(new_annotation)
            await session.commit()
            await session.refresh(new_annotation)
            
            return AnnotationResponse.model_validate(new_annotation).model_dump()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create annotation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{annotation_id}", summary="Update annotation")
async def update_annotation(
    annotation_id: str,
    update: AnnotationUpdate,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Update an annotation (add note, change color, etc.)."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Annotation
        
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(Annotation).where(Annotation.id == annotation_id)
            )
            annotation = result.scalar_one_or_none()
            
            if not annotation:
                raise HTTPException(status_code=404, detail="Annotation not found")
            
            # Update fields
            if update.note is not None:
                annotation.note = update.note
            if update.highlight_color is not None:
                annotation.highlight_color = update.highlight_color
            if update.is_deleted is not None:
                annotation.is_deleted = update.is_deleted
            
            annotation.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(annotation)
            
            return AnnotationResponse.model_validate(annotation).model_dump()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update annotation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{annotation_id}", summary="Delete annotation")
async def delete_annotation(
    annotation_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Soft delete an annotation."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Annotation
        
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(Annotation).where(Annotation.id == annotation_id)
            )
            annotation = result.scalar_one_or_none()
            
            if not annotation:
                raise HTTPException(status_code=404, detail="Annotation not found")
            
            annotation.is_deleted = True
            annotation.updated_at = datetime.utcnow()
            await session.commit()
            
            return {"message": "Annotation deleted"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete annotation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Notes API
# ---------------------------------------------------------------------------

@router.get("/{document_id}/notes", summary="Get notes for document")
async def get_notes(
    document_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get all notes for a document."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Note
        
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(Note).where(
                    Note.document_id == document_id,
                    Note.is_deleted == False,
                ).order_by(Note.page_number, Note.created_at)
            )
            notes = result.scalars().all()
            
            return {
                "document_id": document_id,
                "notes": [NoteResponse.model_validate(n).model_dump() for n in notes],
                "count": len(notes),
            }
            
    except Exception as e:
        logger.error(f"Get notes failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/notes", summary="Create note")
async def create_note(
    document_id: str,
    note: NoteCreate,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Create a new note for a document page."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Note
        
        async with db.async_session_maker() as session:
            # Verify document exists
            doc_result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            if not doc_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Document not found")
            
            note_id = str(uuid.uuid4())
            new_note = Note(
                id=note_id,
                document_id=document_id,
                page_number=note.page_number,
                content=note.content,
                color=note.color or "#FFF9C4",
                tags=note.tags or [],
            )
            
            session.add(new_note)
            await session.commit()
            await session.refresh(new_note)
            
            return NoteResponse.model_validate(new_note).model_dump()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create note failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notes/{note_id}", summary="Update note")
async def update_note(
    note_id: str,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Update a note."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Note
        
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(Note).where(Note.id == note_id)
            )
            note = result.scalar_one_or_none()
            
            if not note:
                raise HTTPException(status_code=404, detail="Note not found")
            
            if content is not None:
                note.content = content
            if tags is not None:
                note.tags = tags
            
            note.updated_at = datetime.utcnow()
            await session.commit()
            
            return NoteResponse.model_validate(note).model_dump()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update note failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}", summary="Delete note")
async def delete_note(
    note_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Soft delete a note."""
    try:
        from sqlalchemy import select
        from backend.models.annotation import Note
        
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(Note).where(Note.id == note_id)
            )
            note = result.scalar_one_or_none()
            
            if not note:
                raise HTTPException(status_code=404, detail="Note not found")
            
            note.is_deleted = True
            note.updated_at = datetime.utcnow()
            await session.commit()
            
            return {"message": "Note deleted"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete note failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
