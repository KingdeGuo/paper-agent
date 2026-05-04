"""
User and authentication models for multi-tenant support.
"""

from sqlalchemy import (
    Column, String, Integer, DateTime, JSON, Boolean, Text
)
from datetime import datetime
from typing import Optional, List, Dict
import uuid

import sys as _sys
import logging as _logging
_logger = _logging.getLogger(__name__)

# Import Base from cluster_database - MUST succeed or we can't proceed
try:
    from paper_agent.backend.services.cluster_database import Base
except ImportError:
    try:
        from backend.services.cluster_database import Base
    except ImportError:
        # Last resort: check if already loaded
        for _mod_name in list(_sys.modules.keys()):
            if 'cluster_database' in _mod_name:
                _mod = _sys.modules[_mod_name]
                if hasattr(_mod, 'Base'):
                    Base = _mod.Base
                    break
        else:
            from sqlalchemy.orm import DeclarativeBase
            Base = type('Base', (DeclarativeBase,), {})()
            _logger.warning("Using fallback Base - table registration may be inconsistent")


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Role and status
    role = Column(String(20), default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Tenant info
    tenant_id = Column(String(36), index=True)
    max_documents = Column(Integer, default=1000)
    max_storage_mb = Column(Integer, default=10240)  # 10GB
    
    # Preferences
    preferences = Column(JSON, default=dict)
    language = Column(String(10), default="en")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # API keys (stored as JSON array)
    api_keys = Column(JSON, default=list)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Optional, Dict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str  # Simplified - use EmailStr if email-validator installed
    full_name: Optional[str] = None
    language: str = "en"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[Dict] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    is_verified: bool = False
    tenant_id: Optional[str] = None
    max_documents: int = 1000
    max_storage_mb: int = 10240
    language: str = "en"
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class APIKeyCreate(BaseModel):
    name: str = Field(..., description="Name/description for this API key")
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
