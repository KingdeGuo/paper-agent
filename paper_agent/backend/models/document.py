"""
Pydantic V2 schemas and SQLAlchemy model for Paper Agent.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Document(Base):
    """SQLAlchemy model for documents."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    title = Column(String)
    authors = Column(JSON)
    year = Column(Integer)
    abstract = Column(Text)
    keywords = Column(JSON)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    upload_date = Column(DateTime, server_default=func.now())
    processed = Column(Integer, default=0)  # 0: pending, 1: processing, 2: completed, 3: failed
    summary = Column(Text)
    vector_id = Column(String)
    doc_metadata = Column(JSON)  # renamed from `metadata` to avoid shadowing Base.metadata


# ---------------------------------------------------------------------------
# Pydantic V2 schemas
# ---------------------------------------------------------------------------


class DocumentCreate(BaseModel):
    """Pydantic model for document creation."""

    filename: str
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    file_path: str
    file_size: int
    arxiv_id: Optional[str] = None
    arxiv_url: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Pydantic model for document updates."""

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Pydantic model for document API responses."""

    id: str
    filename: str
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    file_path: str
    file_size: int
    upload_date: datetime
    processed: int
    summary: Optional[str] = None
    vector_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    arxiv_url: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Search schemas
# ---------------------------------------------------------------------------


class SearchQuery(BaseModel):
    """Pydantic model for search queries."""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Pydantic model for search results."""

    document_id: str
    score: float
    text: str = ""
    highlights: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document: Optional[DocumentResponse] = None


class SearchRequest(BaseModel):
    """Pydantic model for search requests."""

    query: str
    limit: int = 10
    model: Optional[str] = None


# ---------------------------------------------------------------------------
# Summary & Q&A schemas
# ---------------------------------------------------------------------------


class SummaryRequest(BaseModel):
    """Pydantic model for summary generation requests."""

    document_id: str
    max_length: int = Field(default=300, ge=50, le=1000)
    style: str = Field(default="academic", pattern="^(academic|simple|detailed)$")
    model: Optional[str] = None


class SummaryResponse(BaseModel):
    """Pydantic model for summary responses."""

    document_id: str
    summary: str
    length: int = 0
    style: str = "academic"
    generated_at: datetime = Field(default_factory=datetime.now)


class QuestionRequest(BaseModel):
    """Pydantic model for question-answering requests."""

    document_id: str
    question: str
    model: Optional[str] = None
