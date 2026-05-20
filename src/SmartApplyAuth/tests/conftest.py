import os
import pytest
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

# Must be set before any app import
os.environ.setdefault("GOOGLE_CLIENT_ID", "fake_client_id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "fake_secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost/auth/callback")
os.environ.setdefault("JWT_SECRET_KEY", "ci_test_fallback_key_32_chars_min")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "test_db")


@pytest.fixture
def mock_user():
    from app.models.user import User
    return User(
        google_id="gid_test_123",
        email="test@example.com",
        name="Test User",
        picture="https://pic.url/img.jpg",
        access_token="access_tok",
        refresh_token="refresh_tok",
        token_expiry=datetime(2030, 1, 1),
        scopes=["gmail.readonly"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def client(mock_user):
    with patch("app.main.create_indexes"):
        from app.main import app
        from app.services.auth.dependency import get_current_user
        app.dependency_overrides[get_current_user] = lambda: mock_user
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
        app.dependency_overrides.clear()


@pytest.fixture
def unauth_client():
    with patch("app.main.create_indexes"):
        from app.main import app
        from app.services.auth.dependency import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
