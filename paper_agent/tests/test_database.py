"""Tests for database service."""

import pytest
import uuid
from paper_agent.backend.services.cluster_database import ClusterDatabaseService
from sqlalchemy import select


@pytest.fixture
async def db():
    service = ClusterDatabaseService()
    service.create_tables()
    yield service


class TestDocumentCRUD:
    @pytest.mark.asyncio
    async def test_create_document(self, db):
        doc = await db.create_document({
            "filename": "test.pdf",
            "title": "Test Paper",
            "authors": ["Author A"],
            "year": 2024,
            "file_path": "/tmp/test.pdf",
            "file_size": 1024,
        })
        assert doc is not None
        assert doc.title == "Test Paper"
        assert doc.authors == ["Author A"]

    @pytest.mark.asyncio
    async def test_get_document(self, db):
        doc = await db.create_document({
            "filename": "get_test.pdf", "file_path": "/tmp/get_test.pdf",
        })
        fetched = await db.get_document(doc.id)
        assert fetched is not None
        assert fetched.id == doc.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, db):
        doc = await db.get_document("nonexistent-id")
        assert doc is None

    @pytest.mark.asyncio
    async def test_update_document(self, db):
        doc = await db.create_document({
            "filename": "update_test.pdf", "file_path": "/tmp/u.pdf",
            "title": "Original",
        })
        updated = await db.update_document(doc.id, {"title": "Updated Title"})
        assert updated.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_soft_delete(self, db):
        doc = await db.create_document({
            "filename": "delete_test.pdf", "file_path": "/tmp/d.pdf",
        })
        deleted = await db.delete_document(doc.id)
        assert deleted is True
        fetched = await db.get_document(doc.id)
        assert fetched is None  # Soft delete filters out

    @pytest.mark.asyncio
    async def test_get_documents_pagination(self, db):
        for i in range(5):
            await db.create_document({
                "filename": f"doc_{i}.pdf", "file_path": f"/tmp/{i}.pdf",
            })
        docs = await db.get_documents(limit=3)
        assert len(docs) <= 3

    @pytest.mark.asyncio
    async def test_search_documents(self, db):
        await db.create_document({
            "filename": "s.pdf", "file_path": "/tmp/s.pdf",
            "title": "Machine Learning Transformers",
            "abstract": "A paper about transformer architectures",
        })
        results = await db.search_documents("transformer")
        assert len(results) >= 1
        assert any("transformer" in (r.title or "").lower() or "transformer" in (r.abstract or "").lower() for r in results)


class TestProcessingStats:
    @pytest.mark.asyncio
    async def test_processing_stats(self, db):
        stats = await db.get_processing_stats()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "pending" in stats
        assert "completed" in stats
