"""
Test backend functionality directly.
"""
import asyncio
import sys
sys.path.insert(0, '/Users/kingdeguo/Downloads/同步空间/codes/paper_agent')

from paper_agent.backend.services.cluster_database import ClusterDatabaseService, User
from paper_agent.backend.services.auth_service import auth_service

async def test_user_system():
    print("=== Testing User System ===")
    
    # Create tables
    print("\n1. Creating database tables...")
    db = ClusterDatabaseService()
    db.create_tables()
    print("   ✓ Tables created")
    
    # Test password hashing
    print("\n2. Testing password hashing...")
    password = "password123"
    hashed = auth_service.hash_password(password)
    print(f"   ✓ Password hashed: {hashed[:20]}...")
    
    verify_result = auth_service.verify_password(password, hashed)
    print(f"   ✓ Password verified: {verify_result}")
    
    # Create test user
    print("\n3. Creating test user...")
    import uuid
    user_id = str(uuid.uuid4())
    
    async with db.async_session_maker() as session:
        # Check if user exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "testuser")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("   ✓ User already exists")
            user = existing
        else:
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
    
    # Test JWT token
    print("\n4. Testing JWT token...")
    token = auth_service.create_access_token({
        "sub": user.id,
        "username": user.username,
    })
    print(f"   ✓ Token created: {token[:30]}...")
    
    # Decode token
    payload = auth_service.decode_token(token)
    print(f"   ✓ Token decoded: user_id={payload.get('sub')}")
    
    print("\n=== User System Ready! ===")

# Run test
asyncio.run(test_user_system())
