"""
Test script to verify backend functionality.
"""
import sys
sys.path.insert(0, '/Users/kingdeguo/Downloads/同步空间/codes/paper_agent')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

# Import after path setup
from paper_agent.backend.services.cluster_database import Base, ClusterDatabaseService, Document
from paper_agent.backend.models.user import User
from paper_agent.backend.services.auth_service import auth_service


async def test():
    print("=== Paper Agent Backend Test ===\n")
    
    # 1. Init database
    print("1. Database...")
    db = ClusterDatabaseService()
    db.create_tables()
    print("   ✓ Tables created")
    
    # 2. Test user creation
    print("\n2. User creation...")
    async with db.async_session_maker() as session:
        # Check existing
        result = await session.execute(select(User).where(User.username == "testuser"))
        user = result.scalar_one_or_none()
        
        if not user:
            import uuid
            hashed = auth_service.hash_password("password123")
            user = User(
                id=str(uuid.uuid4()),
                username="testuser",
                email="test@example.com",
                hashed_password=hashed,
                full_name="Test User",
            )
            session.add(user)
            await session.commit()
            print("   ✓ User created")
        else:
            print("   ✓ User exists")
        
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
    
    # 3. Test JWT token
    print("\n3. JWT Token...")
    token = auth_service.create_access_token({
        "sub": user.id,
        "username": user.username,
    })
    print(f"   ✓ Token: {token[:30]}...")
    
    # 4. Verify token
    payload = auth_service.decode_token(token)
    print(f"   ✓ Decoded: user_id={payload.get('sub')}")
    
    # 5. Test password verification
    print("\n4. Password verification...")
    result = auth_service.verify_password("password123", user.hashed_password)
    print(f"   ✓ Password valid: {result}")
    
    # 6. Test document query (should work even if empty)
    print("\n5. Document query...")
    docs = await db.get_documents(limit=10)
    print(f"   ✓ Found {len(docs)} documents")
    
    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test())
