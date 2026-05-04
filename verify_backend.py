"""Backend verification script - end-to-end health check."""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from paper_agent.backend.services.cluster_database import ClusterDatabaseService
from paper_agent.backend.models.user import User
from paper_agent.backend.services.auth_service import (
    hash_password, verify_password, create_access_token, decode_token,
)


async def verify():
    print("=== Paper Agent Backend Verification ===\n")

    print("1. Auth service...")
    hashed = hash_password("password123")
    assert verify_password("password123", hashed)
    token = create_access_token({"sub": "v-user", "username": "verifier"})
    payload = decode_token(token)
    assert payload and payload["sub"] == "v-user"
    print("   ✓ Auth service operational")

    print("2. Database...")
    db = ClusterDatabaseService()
    db.create_tables()
    docs = await db.get_documents(limit=5)
    print(f"   ✓ Database operational ({len(docs)} documents)")

    print("3. Document operations...")
    doc = await db.create_document({
        "filename": "test_doc.pdf",
        "title": "Verification Test Paper",
        "file_path": "/tmp/test_doc.pdf",
    })
    assert doc is not None
    print(f"   ✓ Document created ({doc.id[:8]}...)")

    fetched = await db.get_document(doc.id)
    assert fetched is not None
    await db.update_document(doc.id, {"title": "Verified Paper"})
    updated = await db.get_document(doc.id)
    assert updated.title == "Verified Paper"
    await db.delete_document(doc.id)
    deleted = await db.get_document(doc.id)
    assert deleted is None  # soft-deleted but filtered out
    print("   ✓ Full CRUD cycle verified")

    print("4. Search...")
    results = await db.search_documents("test")
    print(f"   ✓ Search operational ({len(results)} results)")

    print("5. Stats...")
    stats = await db.get_processing_stats()
    print(f"   ✓ Stats: {stats}")

    await db.close()
    print("\n=== All systems verified! ===")


if __name__ == "__main__":
    asyncio.run(verify())
