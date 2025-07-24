from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

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
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Integer, default=0)  # 0: pending, 1: processing, 2: completed, 3: failed
    summary = Column(Text)
    vector_id = Column(String)
    metadata = Column(JSON)

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

class DocumentResponse(BaseModel):
    """Pydantic model for document response."""
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
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    """Pydantic model for document updates."""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchQuery(BaseModel):
    """Pydantic model for search queries."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Pydantic model for search results."""
    document: DocumentResponse
    score: float
    highlights: Optional[List[str]] = None

class SummaryRequest(BaseModel):
    """Pydantic model for summary generation requests."""
    document_id: str
    max_length: int = Field(default=300, ge=50, le=1000)
    style: str = Field(default="academic", regex="^(academic|simple|detailed)$")

class SummaryResponse(BaseModel):
    """Pydantic model for summary responses."""
    document_id: str
    summary: str
    length: int
    style: str
    generated_at: datetime

class DocumentBase(BaseModel):
    title: str
    authors: List[str] = []
    year: Optional[int] = None
    keywords: List[str] = []
    abstract: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    keywords: Optional[List[str]] = None
    abstract: Optional[str] = None

class Document(DocumentBase):
    id: str
    file_path: str
    text: Optional[str] = None
    summary: Optional[str] = None
    summary_style: Optional[str] = "academic"
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SummaryRequest(BaseModel):
    document_id: str
    max_length: int = 300
    style: str = "academic"
    model: Optional[str] = None  # 添加模型选择字段

class SummaryResponse(BaseModel):
    document_id: str
    summary: str
    length: Optional[int] = None
    style: str = "academic"

class QuestionRequest(BaseModel):
    document_id: str
    question: str
    model: Optional[str] = None  # 添加模型选择字段

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    model: Optional[str] = None  # 添加模型选择字段

class SearchResult(BaseModel):
    document_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    score: float
    excerpt: str
