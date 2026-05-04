"""Backend unit tests."""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from paper_agent.backend.services.auth_service import (
    hash_password, verify_password, create_access_token, decode_token,
)


def test_password_hashing():
    password = "password123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)
    print("  ✓ Password hashing with PBKDF2-SHA256")


def test_jwt_token():
    token = create_access_token({"sub": "test-user-id", "username": "testuser"})
    assert token
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test-user-id"
    assert payload["username"] == "testuser"
    print("  ✓ JWT token creation and verification")

    # Invalid token
    assert decode_token("invalid.token.here") is None
    print("  ✓ Invalid token rejection")


def test_database():
    from paper_agent.backend.services.cluster_database import ClusterDatabaseService
    db = ClusterDatabaseService()
    db.create_tables()
    print("  ✓ Tables created")

    doc_id = asyncio.run(_test_document_crud(db))
    print(f"  ✓ Document CRUD (id={doc_id[:8]}...)")

    stats = asyncio.run(db.get_processing_stats())
    print(f"  ✓ Processing stats: {stats}")

    asyncio.run(db.delete_document(doc_id))
    print("  ✓ Soft delete")


async def _test_document_crud(db):
    doc = await db.create_document({
        "filename": "test.pdf",
        "title": "Test Paper",
        "authors": ["Test Author"],
        "year": 2024,
        "abstract": "Test abstract",
        "keywords": ["test"],
        "file_path": "/tmp/test.pdf",
        "file_size": 1024,
        "processed": 0,
    })
    assert doc is not None
    doc_id = doc.id

    fetched = await db.get_document(doc_id)
    assert fetched is not None
    assert fetched.title == "Test Paper"

    docs = await db.get_documents(limit=10)
    assert len(docs) > 0

    await db.update_document(doc_id, {"title": "Updated Paper"})
    updated = await db.get_document(doc_id)
    assert updated.title == "Updated Paper"

    results = await db.search_documents("test")
    assert len(results) > 0

    return doc_id


if __name__ == "__main__":
    print("=== Paper Agent Backend Tests ===\n")
    print("1. Auth:")
    test_password_hashing()
    test_jwt_token()
    print()
    print("2. Database:")
    test_database()
    print()
    print("=== All tests passed! ===")
