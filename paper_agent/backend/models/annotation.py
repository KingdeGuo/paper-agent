"""
Annotation and note models for PDF viewer.
"""

from sqlalchemy import (
    Column, String, Integer, DateTime, JSON, Boolean, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List
import uuid

from backend.services.cluster_database import Base


# ---------------------------------------------------------------------------
# Annotation model (text highlights)
# ---------------------------------------------------------------------------

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    
    # Highlight data
    text = Column(Text)  # Highlighted text
    highlight_color = Column(String(20), default="#FFEB3B")  # Yellow default
    
    # Position (for rendering)
    position_x = Column(Integer)
    position_y = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    
    # Note attached to highlight
    note = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # Relationship
    document = relationship("Document", back_populates="annotations")


# ---------------------------------------------------------------------------
# Note model (page notes/comments)
# ---------------------------------------------------------------------------

class Note(Base):
    __tablename__ = "notes"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    
    # Note content
    content = Column(Text, nullable=False)
    color = Column(String(20), default="#FFF9C4")  # Light yellow
    tags = Column(JSON, default=list)  # ["important", "method", etc.]
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # Relationship
    document = relationship("Document", back_populates="notes")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class AnnotationBase(BaseModel):
    page_number: int
    text: str
    highlight_color: Optional[str] = "#FFEB3B"
    note: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class AnnotationCreate(AnnotationBase):
    pass


class AnnotationUpdate(BaseModel):
    note: Optional[str] = None
    highlight_color: Optional[str] = None
    is_deleted: Optional[bool] = None


class AnnotationResponse(AnnotationBase):
    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    page_number: int
    content: str
    color: Optional[str] = "#FFF9C4"
    tags: Optional[List[str]] = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    is_deleted: Optional[bool] = None


class NoteResponse(NoteBase):
    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
