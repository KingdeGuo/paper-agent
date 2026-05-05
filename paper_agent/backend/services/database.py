import logging
import os
import uuid
from typing import Dict, List, Optional

from backend.config.settings import settings
from backend.models.document import Document, DocumentCreate, DocumentResponse, DocumentUpdate
from sqlalchemy import create_engine, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations."""

    def __init__(self):
        self.database_url = "sqlite+aiosqlite:///./data/documents.db"
        self.sync_database_url = "sqlite:///./data/documents.db"

        # Create async engine
        self.async_engine = create_async_engine(
            self.database_url,
            echo=settings.server.debug,
        )

        # Create sync engine for migrations
        self.sync_engine = create_engine(
            self.sync_database_url,
            echo=settings.server.debug,
        )

        # Create session makers
        self.async_session_maker = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.sync_session_maker = sessionmaker(
            bind=self.sync_engine,
            expire_on_commit=False,
        )

    def create_tables(self):
        """Create database tables."""
        Document.metadata.create_all(self.sync_engine)
        logger.info("Database tables created")

    async def create_document(self, document: DocumentCreate) -> DocumentResponse:
        """Create a new document record."""
        async with self.async_session_maker() as session:
            doc_id = str(uuid.uuid4())

            db_document = Document(
                id=doc_id,
                filename=document.filename,
                title=document.title,
                authors=document.authors,
                year=document.year,
                abstract=document.abstract,
                keywords=document.keywords,
                file_path=document.file_path,
                file_size=document.file_size,
                arxiv_id=document.arxiv_id,
                arxiv_url=document.arxiv_url,
                processed=0,
            )

            session.add(db_document)
            await session.commit()
            await session.refresh(db_document)

            return DocumentResponse.model_validate(db_document)

    async def get_document_by_arxiv_id(self, arxiv_id: str) -> Optional[DocumentResponse]:
        """Get document by arXiv ID."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.arxiv_id == arxiv_id)
            )
            document = result.scalar_one_or_none()

            if document:
                return DocumentResponse.model_validate(document)
            return None

    async def update_document_path(self, document_id: str, file_path: str) -> bool:
        """Update document file path."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                return False

            document.file_path = file_path
            await session.commit()
            return True

    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """Get document by ID."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if document:
                return DocumentResponse.model_validate(document)
            return None

    async def get_all_documents(
        self, skip: int = 0, limit: int = 100
    ) -> List[DocumentResponse]:
        """Get all documents with pagination."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document)
                .order_by(Document.upload_date.desc())
                .offset(skip)
                .limit(limit)
            )
            documents = result.scalars().all()

            return [DocumentResponse.model_validate(doc) for doc in documents]

    async def update_document(
        self, document_id: str, update_data: DocumentUpdate
    ) -> Optional[DocumentResponse]:
        """Update document."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                return None

            # Update fields
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(document, field, value)

            await session.commit()
            await session.refresh(document)

            return DocumentResponse.model_validate(document)

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
            document = result.scalar_one_or_none()

            if not document:
                return False

            document.processed = status
            if summary is not None:
                document.summary = summary
            if vector_id is not None:
                document.vector_id = vector_id

            await session.commit()
            return True

    async def delete_document(self, document_id: str) -> bool:
        """Delete document."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                return False

            # Delete file
            try:
                if os.path.exists(document.file_path):
                    os.remove(document.file_path)
            except Exception as e:
                logger.error(f"Error deleting file {document.file_path}: {str(e)}")

            # Delete from database
            await session.delete(document)
            await session.commit()

            return True

    async def search_documents(
        self, query: str, limit: int = 10
    ) -> List[DocumentResponse]:
        """Search documents by title, authors, or keywords."""
        async with self.async_session_maker() as session:
            search_pattern = f"%{query}%"

            result = await session.execute(
                select(Document)
                .where(
                    Document.title.ilike(search_pattern)
                    | Document.authors.ilike(search_pattern)
                    | Document.keywords.ilike(search_pattern)
                    | Document.abstract.ilike(search_pattern)
                )
                .order_by(Document.upload_date.desc())
                .limit(limit)
            )

            documents = result.scalars().all()
            return [DocumentResponse.model_validate(doc) for doc in documents]

    async def get_processing_stats(self) -> Dict[str, int]:
        """Get document processing statistics."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document.processed, func.count(Document.id)).group_by(
                    Document.processed
                )
            )

            stats: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
            for status, count in result.all():
                stats[status] = count

            return {
                "pending": stats[0],
                "processing": stats[1],
                "completed": stats[2],
                "failed": stats[3],
                "total": sum(stats.values()),
            }

    async def get_recent_documents(self, limit: int = 10) -> List[DocumentResponse]:
        """Get recent documents."""
        return await self.get_all_documents(limit=limit)

    async def get_documents_by_year(self, year: int) -> List[DocumentResponse]:
        """Get documents by year."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document)
                .where(Document.year == year)
                .order_by(Document.upload_date.desc())
            )

            documents = result.scalars().all()
            return [DocumentResponse.model_validate(doc) for doc in documents]

    async def get_documents_by_author(
        self, author: str
    ) -> List[DocumentResponse]:
        """Get documents by author."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(Document)
                .where(Document.authors.contains(author))
                .order_by(Document.upload_date.desc())
            )

            documents = result.scalars().all()
            return [DocumentResponse.model_validate(doc) for doc in documents]
