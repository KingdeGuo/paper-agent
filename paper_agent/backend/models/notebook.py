"""
Models for Research Notebook and Zotero integration.
"""

import logging as _logging
import sys as _sys
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

_logger = _logging.getLogger(__name__)

try:
    from paper_agent.backend.services.cluster_database import Base
except ImportError:
    try:
        from backend.services.cluster_database import Base
    except ImportError:
        for _mod_name in list(_sys.modules.keys()):
            if 'cluster_database' in _mod_name:
                _mod = _sys.modules[_mod_name]
                if hasattr(_mod, 'Base'):
                    Base = _mod.Base
                    break
        else:
            from sqlalchemy.orm import DeclarativeBase
            Base = type('Base', (DeclarativeBase,), {})()
            _logger.warning("Using fallback Base for notebook models")
# Research Notebook & Discovery
# ---------------------------------------------------------------------------

class Notebook(Base):
    """A research notebook for a user."""
    __tablename__ = "notebooks"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    # New: Visibility for collaboration
    visibility = Column(String(20), default="private")  # private, shared, public
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)


class NotebookEntry(Base):
    """An entry in a research notebook."""
    __tablename__ = "notebook_entries"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True)
    notebook_id = Column(String(36), index=True, nullable=False)
    document_id = Column(String(36), index=True)  # Optional link to a specific paper
    type = Column(String(50), default="note")  # note, snippet, draft, insight, hypothesis, contradiction
    content = Column(Text, nullable=False)
    # New: Structured AI findings
    source_nodes = Column(JSON, default=list)  # References to specific parts of papers
    confidence_score = Column(Integer)  # For AI-generated insights
    doc_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResearchThread(Base):
    """Persisted AI conversation focused on a research goal."""
    __tablename__ = "research_threads"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True, nullable=False)
    notebook_id = Column(String(36), index=True)
    goal = Column(String(500), nullable=False)  # e.g., "Find contradictions in Transformer efficiency"
    context_docs = Column(JSON, default=list)  # List of document_ids
    messages = Column(JSON, default=list)  # History of the thread
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# ---------------------------------------------------------------------------
# Zotero Integration
# ---------------------------------------------------------------------------

class ZoteroCredential(Base):
    """Zotero API credentials for a user."""
    __tablename__ = "zotero_credentials"
    __table_args__ = {"extend_existing": True}

    user_id = Column(String(36), primary_key=True)
    zotero_user_id = Column(String(50), nullable=False)
    api_key = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    config = Column(JSON, default=dict)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class NotebookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class NotebookEntryCreate(BaseModel):
    notebook_id: str
    document_id: Optional[str] = None
    type: str = "note"
    content: str
    metadata: Optional[Dict] = None


class ZoteroConnectRequest(BaseModel):
    zotero_user_id: str
    api_key: str
