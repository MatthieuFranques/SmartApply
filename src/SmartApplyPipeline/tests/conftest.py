"""Shared test config for the Pipeline microservice.

Fake env vars + FastAPI fixtures. TestClient is created without entering the
lifespan (no `with`), so startup's create_indexes()/Mongo connection never runs.
"""

import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "smartapply_test")
os.environ.setdefault("GMAIL_URL", "http://gmail:8004")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth.dependency import get_current_user, AuthUser


FAKE_AUTH = AuthUser(google_id="google_123", email="test@gmail.com", name="Test User")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client():
    app.dependency_overrides[get_current_user] = lambda: FAKE_AUTH
    yield TestClient(app)
    app.dependency_overrides.clear()
