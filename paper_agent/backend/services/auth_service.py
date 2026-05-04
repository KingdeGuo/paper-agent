"""
Authentication service - enterprise-grade security.

Uses JWT for tokens and PBKDF2-SHA256 with salt for password hashing.
"""

import os
import logging
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("PAPER_AGENT_SECRET_KEY", "paper-agent-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
PBKDF2_ITERATIONS = 600_000


# ---------------------------------------------------------------------------
# Password handling (PBKDF2-SHA256 with salt)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256 with random salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored PBKDF2 hash."""
    try:
        salt_hex, key_hex = hashed_password.split("$")
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return new_key == stored_key
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# JWT Tokens
# ---------------------------------------------------------------------------

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


# ---------------------------------------------------------------------------
# API Key management
# ---------------------------------------------------------------------------

def generate_api_key() -> Dict[str, str]:
    """
    Generate an API key.
    Returns dict with full_key, key_hash, key_prefix.
    """
    raw_key = f"pa_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12] + "..."
    return {
        "full_key": raw_key,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
    }


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against stored hash."""
    return hashlib.sha256(api_key.encode()).hexdigest() == stored_hash


# ---------------------------------------------------------------------------
# Auth Service class (for backward compatibility)
# ---------------------------------------------------------------------------

class AuthService:
    """Legacy class wrapper - use functions directly."""
    
    def create_access_token(self, data, expires_delta=None):
        return create_access_token(data, expires_delta)
    
    def decode_token(self, token):
        return decode_token(token)
    
    def hash_password(self, password):
        return hash_password(password)
    
    def verify_password(self, plain_password, hashed_password):
        return verify_password(plain_password, hashed_password)
    
    def generate_api_key(self):
        return generate_api_key()
    
    def verify_api_key(self, api_key, stored_hash):
        return verify_api_key(api_key, stored_hash)


# Global auth service instance
auth_service = AuthService()
