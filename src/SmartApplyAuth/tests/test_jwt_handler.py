import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.services.auth.jwt_handler import create_jwt, decode_jwt, get_secret_key, ALGORITHM


def test_create_jwt_returns_str():
    assert isinstance(create_jwt("gid_123"), str)


def test_create_jwt_encodes_sub_claim():
    token = create_jwt("gid_abc")
    payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
    assert payload["sub"] == "gid_abc"


def test_create_jwt_expires_in_7_days():
    token = create_jwt("gid_123")
    payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
    exp = datetime.utcfromtimestamp(payload["exp"])
    assert timedelta(days=6) < (exp - datetime.utcnow()) <= timedelta(days=7)


def test_decode_jwt_valid_token_returns_google_id():
    token = create_jwt("gid_xyz")
    assert decode_jwt(token) == "gid_xyz"


def test_decode_jwt_garbage_returns_none():
    assert decode_jwt("not.a.valid.token") is None


def test_decode_jwt_expired_token_returns_none():
    payload = {"sub": "gid_123", "exp": datetime.utcnow() - timedelta(seconds=1)}
    token = jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM)
    assert decode_jwt(token) is None


def test_decode_jwt_wrong_secret_returns_none():
    payload = {"sub": "gid_123", "exp": datetime.utcnow() + timedelta(days=7)}
    token = jwt.encode(payload, "wrong_secret_key", algorithm=ALGORITHM)
    assert decode_jwt(token) is None
