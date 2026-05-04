"""
Authentication middleware for protecting API endpoints.
"""

import logging
from typing import Optional, Callable
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.services.auth_service import auth_service
from backend.models.user import UserResponse

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserResponse]:
    """
    Get current user from JWT token.
    Returns None if not authenticated (for optional auth).
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # Get user from database
    from backend.services.cluster_database import ClusterDatabaseService
    from sqlalchemy import select
    from backend.models.user import User
    
    db = ClusterDatabaseService()
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return UserResponse.model_validate(user)


async def require_user(
    user: Optional[UserResponse] = Depends(get_current_user_from_token),
) -> UserResponse:
    """
    Dependency that requires authentication.
    Raises 401 if not authenticated.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_admin(
    user: UserResponse = Depends(require_user),
) -> UserResponse:
    """
    Dependency that requires admin role.
    Raises 403 if not admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# Optional auth - returns user if authenticated, None otherwise
get_optional_user = get_current_user_from_token
