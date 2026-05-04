"""
User authentication and management routes.

Supports:
- User registration and login
- JWT token authentication
- API key management
- User profile management
"""

import os
import sys
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from paper_agent.backend.models.user import (
        UserCreate, UserLogin, UserResponse, UserUpdate,
        Token, APIKeyCreate, APIKeyResponse
    )
except ImportError:
    try:
        from backend.models.user import (
            UserCreate, UserLogin, UserResponse, UserUpdate,
            Token, APIKeyCreate, APIKeyResponse
        )
    except ImportError:
        UserCreate = UserLogin = UserResponse = UserUpdate = None
        Token = APIKeyCreate = APIKeyResponse = None
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_db():
    """Get database service from registry."""
    from paper_agent.backend.services.registry import get_db as _get_db
    return _get_db()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Get user from database
    try:
        from sqlalchemy import select
        from paper_agent.backend.models.user import User
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found or inactive")
            
            return UserResponse.model_validate(user)
    except ImportError:
        raise HTTPException(status_code=500, detail="User model not available")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    try:
        from sqlalchemy import select
        from paper_agent.backend.models.user import User
    except ImportError:
        try:
            from sqlalchemy import select
            from backend.models.user import User
        except ImportError:
            raise HTTPException(status_code=500, detail="User model not available")
    
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db.async_session_maker() as session:
        # Check if username exists
        result = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email exists
        result = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = auth_service.hash_password(user_data.password)
        
        user = User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            language=user_data.language,
            tenant_id=user_data.username,  # Simple tenant assignment
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        logger.info(f"User registered: {user.username}")
        return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: ClusterDatabaseService = Depends(get_db)):
    """Login and get JWT token."""
    from sqlalchemy import select
    from backend.models.user import User
    
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(User).where(
                (User.username == credentials.username) | 
                (User.email == credentials.username)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user or not auth_service.verify_password(credentials.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="User account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await session.commit()
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )
        
        logger.info(f"User logged in: {user.username}")
        return Token(access_token=access_token, expires_in=60*60*24)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Update current user profile."""
    from sqlalchemy import select
    from backend.models.user import User
    
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.language is not None:
            user.language = update_data.language
        if update_data.preferences is not None:
            user.preferences = update_data.preferences
        
        user.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        
        return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# API Key management
# ---------------------------------------------------------------------------

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Create a new API key."""
    from sqlalchemy import select
    from backend.models.user import User
    
    full_key, key_hash, key_prefix = auth_service.generate_api_key()
    
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Add API key to user
        api_key_entry = {
            "id": str(uuid.uuid4()),
            "name": key_data.name,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + timedelta(days=key_data.expires_days)
            ).isoformat() if key_data.expires_days else None,
            "last_used": None,
        }
        
        if not user.api_keys:
            user.api_keys = []
        user.api_keys.append(api_key_entry)
        await session.commit()
        
        # Return full key only once
        return APIKeyResponse(
            id=api_key_entry["id"],
            name=api_key_entry["name"],
            key_prefix=key_prefix,
            created_at=datetime.fromisoformat(api_key_entry["created_at"]),
            expires_at=datetime.fromisoformat(api_key_entry["expires_at"]) if api_key_entry["expires_at"] else None,
            last_used=None,
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """List user's API keys."""
    from sqlalchemy import select
    from backend.models.user import User
    
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.api_keys:
            return []
        
        return [
            APIKeyResponse(
                id=k["id"],
                name=k["name"],
                key_prefix=k["key_prefix"],
                created_at=datetime.fromisoformat(k["created_at"]),
                expires_at=datetime.fromisoformat(k["expires_at"]) if k.get("expires_at") else None,
                last_used=datetime.fromisoformat(k["last_used"]) if k.get("last_used") else None,
            )
            for k in user.api_keys
        ]


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: ClusterDatabaseService = Depends(get_db),
):
    """Delete an API key."""
    from sqlalchemy import select
    from backend.models.user import User
    
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.api_keys:
            raise HTTPException(status_code=404, detail="API key not found")
        
        user.api_keys = [k for k in user.api_keys if k["id"] != key_id]
        await session.commit()
        
        return {"message": "API key deleted"}
