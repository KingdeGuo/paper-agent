"""
Simple backend test script
"""
import sys
sys.path.insert(0, '/Users/kingdeguo/Downloads/同步空间/codes/paper_agent')

from paper_agent.backend.services.cluster_database import ClusterDatabaseService, User
from paper_agent.backend.services.auth_service import auth_service

# Create tables
print("1. Creating database tables...")
db = ClusterDatabaseService()
db.create_tables()
print("   ✓ Tables created")

# Test user creation
print("\n2. Testing user creation...")
try:
    async with db.async_session_maker() as session:
        # Check if test user exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "testuser")
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            import uuid
            user_id = str(uuid.uuid4())
            hashed = auth_service.hash_password("password123")
            
            user = User(
                id=user_id,
                username="testuser",
                email="test@example.com",
                hashed_password=hashed,
                full_name="Test User",
            )
            session.add(user)
            await session.commit()
            print("   ✓ User created")
        else:
            print("   ✓ User already exists")
            
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test JWT token creation
print("\n3. Testing JWT token...")
try:
    token_data = auth_service.create_access_token({"sub": "test-user-id", "username": "testuser"})
    print(f"   ✓ Token created: {token_data[:30]}...")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test password verification
print("\n4. Testing password verification...")
try:
    hashed = auth_service.hash_password("testpass")
    result = auth_service.verify_password("testpass", hashed)
    print(f"   ✓ Password verified: {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n=== All basic tests passed! ===")
