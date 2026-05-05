"""
Cluster-aware database service.

Supports both SQLite (development) and PostgreSQL (production/cluster).
"""

import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

try:
    from paper_agent.backend.config.cluster_settings import cluster_settings
    from paper_agent.backend.config.settings import settings
except ImportError:
    try:
        from backend.config.cluster_settings import cluster_settings
        from backend.config.settings import settings
    except ImportError:
        # Fallback - create dummy settings
        class DummySettings:
            class Server:
                debug = False
            server = Server()
        settings = DummySettings()

        class DummyClusterSettings:
            enable_clustering = False
            node_id = "local-1"
            database = type('DatabaseSettings', (), {'type': 'sqlite', 'sqlite_path': './data/documents.db', 'async_url': 'sqlite+aiosqlite:///./data/documents.db', 'sync_url': 'sqlite:///./data/documents.db'})()
            redis = type('RedisSettings', (), {'enabled': False})()
            storage = type('StorageSettings', (), {'enabled': False})()
            task_queue = type('TaskQueueSettings', (), {'type': 'none'})()
        cluster_settings = DummyClusterSettings()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Document model (cluster-aware)
# ---------------------------------------------------------------------------

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(500))
    authors = Column(JSON, default=list)
    year = Column(Integer)
    abstract = Column(Text)
    keywords = Column(JSON, default=list)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Integer, default=0)  # 0=pending, 1=processing, 2=completed, 3=failed
    summary = Column(Text)
    vector_id = Column(String(255))
    doc_metadata = Column(JSON, default=dict)

    # arXiv fields
    arxiv_id = Column(String(50))
    arxiv_url = Column(String(500))

    # Cluster fields
    user_id = Column(String(36), default="default")  # For multi-tenant
    tenant_id = Column(String(36), default="default")
    node_id = Column(String(50))  # Which node processed this
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)


# ---------------------------------------------------------------------------
# Database Service
# ---------------------------------------------------------------------------

class ClusterDatabaseService:
    """Database service with cluster support."""

    def __init__(self):
        self.config = cluster_settings.database
        self._async_engine = None
        self._sync_engine = None
        self._async_session_maker = None
        self._sync_session_maker = None

    @property
    def async_engine(self):
        if self._async_engine is None:
            kwargs = {}
            if self.config.type == "postgresql":
                kwargs = {
                    "pool_size": self.config.pool_size,
                    "max_overflow": self.config.max_overflow,
                    "pool_recycle": self.config.pool_recycle,
                    "echo": settings.server.debug,
                }
            self._async_engine = create_async_engine(
                self.config.async_url,
                **kwargs
            )
        return self._async_engine

    @property
    def sync_engine(self):
        if self._sync_engine is None:
            kwargs = {}
            if self.config.type == "postgresql":
                kwargs = {
                    "pool_size": self.config.pool_size,
                    "max_overflow": self.config.max_overflow,
                    "pool_recycle": self.config.pool_recycle,
                    "echo": settings.server.debug,
                }
            self._sync_engine = create_engine(
                self.config.sync_url,
                **kwargs
            )
        return self._sync_engine

    @property
    def async_session_maker(self):
        if self._async_session_maker is None:
            self._async_session_maker = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_maker

    @property
    def sync_session_maker(self):
        if self._sync_session_maker is None:
            self._sync_session_maker = sessionmaker(
                bind=self.sync_engine,
                expire_on_commit=False,
            )
        return self._sync_session_maker

    def create_tables(self):
        """Create all tables."""
        try:
            from paper_agent.backend.models.notebook import (
                Notebook,
                NotebookEntry,
                ResearchThread,
                ZoteroCredential,
            )
            from paper_agent.backend.models.user import User
        except ImportError:
            try:
                from backend.models.notebook import (
                    Notebook,
                    NotebookEntry,
                    ResearchThread,
                    ZoteroCredential,
                )
                from backend.models.user import User
            except ImportError:
                logger.warning("Models not found for table creation")

        Base.metadata.create_all(self.sync_engine)
        logger.info(f"Database tables created (type: {self.config.type})")

    async def close(self):
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()

    # -----------------------------------------------------------------------
    # Notebook operations
    # -----------------------------------------------------------------------

    async def create_notebook(self, user_id: str, title: str, description: Optional[str] = None) -> Any:
        try:
            from paper_agent.backend.models.notebook import Notebook
        except ImportError:
            from backend.models.notebook import Notebook

        async with self.async_session_maker() as session:
            notebook = Notebook(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                description=description
            )
            session.add(notebook)
            await session.commit()
            await session.refresh(notebook)
            return notebook

    async def get_user_notebooks(self, user_id: str) -> List[Any]:
        try:
            from paper_agent.backend.models.notebook import Notebook
        except ImportError:
            from backend.models.notebook import Notebook

        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Notebook).where(Notebook.user_id == user_id, not Notebook.is_deleted)
            )
            return list(result.scalars().all())

    async def create_notebook_entry(self, data: Dict[str, Any]) -> Any:
        try:
            from paper_agent.backend.models.notebook import NotebookEntry
        except ImportError:
            from backend.models.notebook import NotebookEntry

        async with self.async_session_maker() as session:
            entry = NotebookEntry(
                id=str(uuid.uuid4()),
                notebook_id=data["notebook_id"],
                document_id=data.get("document_id"),
                type=data.get("type", "note"),
                content=data["content"],
                metadata=data.get("metadata", {})
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

    async def get_notebook_entries(self, notebook_id: str) -> List[Any]:
        try:
            from paper_agent.backend.models.notebook import NotebookEntry
        except ImportError:
            from backend.models.notebook import NotebookEntry

        async with self.async_session_maker() as session:
            result = await session.execute(
                select(NotebookEntry).where(NotebookEntry.notebook_id == notebook_id).order_by(NotebookEntry.created_at.desc())
            )
            return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # Research Thread operations
    # -----------------------------------------------------------------------

    async def create_research_thread(self, user_id: str, goal: str, docs: List[str], notebook_id: Optional[str] = None) -> Any:
        try:
            from paper_agent.backend.models.notebook import ResearchThread
        except ImportError:
            from backend.models.notebook import ResearchThread

        async with self.async_session_maker() as session:
            thread = ResearchThread(
                id=str(uuid.uuid4()),
                user_id=user_id,
                notebook_id=notebook_id,
                goal=goal,
                context_docs=docs,
                messages=[]
            )
            session.add(thread)
            await session.commit()
            await session.refresh(thread)
            return thread

    async def update_thread_messages(self, thread_id: str, messages: List[Dict]) -> bool:
        try:
            from paper_agent.backend.models.notebook import ResearchThread
        except ImportError:
            from backend.models.notebook import ResearchThread

        async with self.async_session_maker() as session:
            result = await session.execute(
                select(ResearchThread).where(ResearchThread.id == thread_id)
            )
            thread = result.scalar_one_or_none()
            if not thread:
                return False

            thread.messages = messages
            thread.updated_at = datetime.utcnow()
            await session.commit()
            return True

    async def get_user_threads(self, user_id: str) -> List[Any]:
        try:
            from paper_agent.backend.models.notebook import ResearchThread
        except ImportError:
            from backend.models.notebook import ResearchThread

        async with self.async_session_maker() as session:
            result = await session.execute(
                select(ResearchThread).where(ResearchThread.user_id == user_id).order_by(ResearchThread.updated_at.desc())
            )
            return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # Document operations
    # -----------------------------------------------------------------------

    async def create_document(self, data: Dict[str, Any]) -> Document:
        """Create a new document."""
        async with self.async_session_maker() as session:
            doc_id = data.get("id") or str(uuid.uuid4())
            node_id = cluster_settings.node_id

            doc = Document(
                id=doc_id,
                filename=data.get("filename", ""),
                title=data.get("title"),
                authors=data.get("authors", []),
                year=data.get("year"),
                abstract=data.get("abstract"),
                keywords=data.get("keywords", []),
                file_path=data.get("file_path", ""),
                file_size=data.get("file_size", 0),
                processed=data.get("processed", 0),
                user_id=data.get("user_id", "default"),
                tenant_id=data.get("tenant_id", "default"),
                node_id=node_id,
            )

            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            return doc

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(
                    Document.id == document_id,
                    not Document.is_deleted
                )
            )
            return result.scalar_one_or_none()

    async def get_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        filters: Optional[Dict] = None,
    ) -> List[Document]:
        """Get documents with pagination and filtering."""
        async with self.async_session_maker() as session:
            query = select(Document).where(not Document.is_deleted)

            if user_id:
                query = query.where(Document.user_id == user_id)

            if filters:
                if filters.get("year"):
                    query = query.where(Document.year == filters["year"])
                if filters.get("status") is not None:
                    query = query.where(Document.processed == filters["status"])

            query = query.order_by(Document.upload_date.desc())
            query = query.offset(skip).limit(limit)

            result = await session.execute(query)
            return list(result.scalars().all())

    # Alias for backward compatibility
    async def get_all_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all documents (alias for backward compatibility)."""
        return await self.get_documents(skip=skip, limit=limit)

    async def update_document(
        self, document_id: str, data: Dict[str, Any]
    ) -> Optional[Document]:
        """Update document."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return None

            for key, value in data.items():
                if hasattr(doc, key) and key not in ("id", "created_at"):
                    setattr(doc, key, value)

            doc.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(doc)
            return doc

    async def delete_document(self, document_id: str) -> bool:
        """Soft delete document."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return False

            # Soft delete
            doc.is_deleted = True
            doc.deleted_at = datetime.utcnow()
            await session.commit()
            return True

    async def search_documents(
        self, query: str, limit: int = 10, user_id: Optional[str] = None
    ) -> List[Document]:
        """Search documents by keyword."""
        async with self.async_session_maker() as session:
            search_pattern = f"%{query}%"

            q = select(Document).where(
                not Document.is_deleted,
                (
                    Document.title.ilike(search_pattern)
                    | Document.abstract.ilike(search_pattern)
                    | Document.keywords.cast(String).ilike(search_pattern)
                )
            )

            if user_id:
                q = q.where(Document.user_id == user_id)

            q = q.order_by(Document.upload_date.desc()).limit(limit)

            result = await session.execute(q)
            return list(result.scalars().all())

    async def get_document_by_arxiv_id(self, arxiv_id: str) -> Optional[Document]:
        """Get document by arXiv ID."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(
                    Document.arxiv_id == arxiv_id,
                    not Document.is_deleted
                )
            )
            return result.scalar_one_or_none()

    async def update_document_path(self, document_id: str, file_path: str) -> bool:
        """Update document file path."""
        return await self.update_document(document_id, {"file_path": file_path})

    async def get_processing_stats(self, user_id: Optional[str] = None) -> Dict[str, int]:
        """Get document processing statistics."""
        async with self.async_session_maker() as session:
            q = select(Document.processed, func.count(Document.id)).where(
                not Document.is_deleted
            )
            if user_id:
                q = q.where(Document.user_id == user_id)

            result = await session.execute(q.group_by(Document.processed))

            stats = {0: 0, 1: 0, 2: 0, 3: 0}
            for status, count in result.all():
                stats[status] = count

            return {
                "pending": stats[0],
                "processing": stats[1],
                "completed": stats[2],
                "failed": stats[3],
                "total": sum(stats.values()),
            }

    async def update_processing_status(
        self,
        document_id: str,
        status: int,
        summary: Optional[str] = None,
        vector_id: Optional[str] = None,
    ) -> bool:
        """Update document processing status."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return False

            doc.processed = status
            if summary is not None:
                doc.summary = summary
            if vector_id is not None:
                doc.vector_id = vector_id
            doc.updated_at = datetime.utcnow()

            await session.commit()
            return True

    async def get_node_stats(self) -> Dict[str, Any]:
        """Get statistics per node (for cluster monitoring)."""
        if not cluster_settings.enable_clustering:
            return {}

        async with self.async_session_maker() as session:
            result = await session.execute(
                select(
                    Document.node_id,
                    func.count(Document.id).label("count"),
                    func.sum(Document.file_size).label("total_size"),
                )
                .where(not Document.is_deleted)
                .group_by(Document.node_id)
            )

            return {
                row.node_id: {
                    "document_count": row.count,
                    "total_size_bytes": row.total_size or 0,
                }
                for row in result.all()
            }
