"""User system integration tests."""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from paper_agent.backend.services.auth_service import (
    hash_password, verify_password, create_access_token, decode_token,
)
from paper_agent.backend.services.cluster_database import ClusterDatabaseService
from paper_agent.backend.models.user import User


async def test_user_system():
    print("=== User System Tests ===\n")

    print("1. Password hashing...")
    password = "password123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)
    print("   ✓ PBKDF2-SHA256 working")

    print("2. Database tables...")
    db = ClusterDatabaseService()
    db.create_tables()
    print("   ✓ Tables created")

    print("3. User creation...")
    import uuid
    from sqlalchemy import select

    user_id = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        user = User(
            id=user_id,
            username="testuser",
            email="test@example.com",
            hashed_password=hashed,
            full_name="Test User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"   ✓ User created: {user.username}")

    print("4. JWT token...")
    token = create_access_token({"sub": user.id, "username": user.username})
    assert token
    print(f"   ✓ Token created")

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user.id
    print(f"   ✓ Token decoded")

    print("5. Cleanup...")
    async with db.async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        u = result.scalar_one_or_none()
        if u:
            await session.delete(u)
            await session.commit()
    print("   ✓ Test user cleaned up")

    print()
    print("=== User System Ready! ===")


if __name__ == "__main__":
    asyncio.run(test_user_system())
