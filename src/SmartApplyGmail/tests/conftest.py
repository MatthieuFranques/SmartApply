"""Shared test config for the Gmail microservice.

Sets fake env vars so modules that capture Google / JWT config at import
time work in CI without real credentials or a database. Must run before any
`app.*` module is imported, which conftest.py guarantees (loaded during
collection, before test modules).
"""

import os
from datetime import datetime, timedelta

os.environ.setdefault("GOOGLE_CLIENT_ID", "fake-client-id.apps.googleusercontent.com")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "fake-client-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:8004/auth/callback")
os.environ.setdefault("JWT_SECRET_KEY", "ci_test_secret_key_at_least_32_chars_long")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "smartapply_test")
os.environ.setdefault("RAG_URL", "http://rag:8001")
os.environ.setdefault("PIPELINE_URL", "http://pipeline:8002")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.services.auth.dependency import get_current_user


FAKE_USER = User(
    id="000000000000000000000000",
    google_id="google_123",
    email="test@gmail.com",
    name="Test User",
    picture=None,
    access_token="fake_access_token",
    refresh_token="fake_refresh_token",
    token_expiry=datetime.utcnow() + timedelta(days=1),
    scopes=["gmail.readonly", "gmail.compose"],
)


@pytest.fixture
def client():
    """TestClient that skips the lifespan (no Mongo connection at startup)."""
    return TestClient(app)


@pytest.fixture
def auth_client():
    """TestClient with get_current_user overridden to a fake authenticated user."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    yield TestClient(app)
    app.dependency_overrides.clear()
