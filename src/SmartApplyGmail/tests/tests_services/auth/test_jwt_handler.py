"""Unit tests for JWT creation / decoding (auth flow)."""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.services.auth import jwt_handler


def test_create_and_decode_roundtrip():
    """A token created for a google_id decodes back to the same id."""
    token = jwt_handler.create_jwt("google_123")
    assert isinstance(token, str)
    assert jwt_handler.decode_jwt(token) == "google_123"


def test_decode_garbage_returns_none():
    """Non-JWT input never raises, returns None."""
    assert jwt_handler.decode_jwt("not-a-jwt") is None
    assert jwt_handler.decode_jwt("") is None


def test_decode_wrong_secret_returns_none():
    """Token signed with another key fails signature check → None."""
    payload = {"sub": "google_123", "exp": datetime.utcnow() + timedelta(days=1)}
    forged = jwt.encode(payload, "some_other_secret_key", algorithm=jwt_handler.ALGORITHM)
    assert jwt_handler.decode_jwt(forged) is None


def test_decode_expired_returns_none():
    """Expired token → None (not an exception)."""
    payload = {"sub": "google_123", "exp": datetime.utcnow() - timedelta(seconds=1)}
    expired = jwt.encode(payload, jwt_handler.get_secret_key(), algorithm=jwt_handler.ALGORITHM)
    assert jwt_handler.decode_jwt(expired) is None


def test_token_has_seven_day_expiry():
    """Payload exp is ~EXPIRE_DAYS in the future."""
    token = jwt_handler.create_jwt("google_123")
    payload = jwt.decode(token, jwt_handler.get_secret_key(), algorithms=[jwt_handler.ALGORITHM])
    exp = datetime.utcfromtimestamp(payload["exp"])
    delta = exp - datetime.utcnow()
    assert timedelta(days=jwt_handler.EXPIRE_DAYS - 1) < delta <= timedelta(days=jwt_handler.EXPIRE_DAYS)
