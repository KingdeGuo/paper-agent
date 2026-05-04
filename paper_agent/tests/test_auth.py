"""Tests for authentication service."""

import pytest
from paper_agent.backend.services.auth_service import (
    hash_password, verify_password,
    create_access_token, decode_token,
)


class TestPasswordHashing:
    def test_hash_returns_different_value(self):
        hashed = hash_password("password123")
        assert hashed != "password123"
        assert "$" in hashed  # salt$hash format

    def test_verify_correct_password(self):
        hashed = hash_password("secure_password")
        assert verify_password("secure_password", hashed)

    def test_verify_wrong_password(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_verify_empty_password(self):
        hashed = hash_password("password")
        assert not verify_password("", hashed)

    def test_different_salts_per_hash(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # Different salts should produce different hashes

    def test_special_characters(self):
        password = "p@$$w0rd!~#[]{}|\\"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_unicode_password(self):
        password = "密码123!@#"
        hashed = hash_password(password)
        assert verify_password(password, hashed)


class TestJWT:
    def test_create_token(self):
        token = create_access_token({"sub": "user-123", "role": "admin"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

    def test_decode_valid_token(self):
        token = create_access_token({"sub": "user-123", "name": "Test"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["name"] == "Test"

    def test_decode_invalid_token(self):
        assert decode_token("invalid.token.here") is None
        assert decode_token("") is None
        assert decode_token("not-a-jwt") is None

    def test_token_expiry(self):
        from datetime import timedelta
        token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(seconds=1))
        payload = decode_token(token)
        assert payload is not None  # Should be valid immediately

    def test_token_contains_expected_claims(self):
        token = create_access_token({"sub": "user-1", "username": "testuser"})
        payload = decode_token(token)
        assert "exp" in payload
        assert "sub" in payload
        assert payload["sub"] == "user-1"

    def test_long_lived_token(self):
        from datetime import timedelta
        token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(days=30))
        payload = decode_token(token)
        assert payload["sub"] == "user-1"
