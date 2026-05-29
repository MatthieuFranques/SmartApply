"""Router tests for /auth (login redirect, OAuth callback, status/me/logout)."""

from unittest.mock import MagicMock, patch

from app.routers import auth as auth_router
from tests.conftest import FAKE_USER


def test_login_redirects_to_google(client):
    resp = client.get("/auth/login", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "accounts.google.com" in resp.headers["location"]


def test_callback_success_sets_cookie_and_redirects(client):
    user_info = {"sub": "google_123", "email": "test@gmail.com", "name": "Test"}
    tokens = {
        "access_token": "at", "refresh_token": "rt",
        "expiry": "2030-01-01T00:00:00", "scopes": ["openid"],
    }
    repo = MagicMock()
    repo.upsert.return_value = FAKE_USER

    with patch.object(auth_router, "exchange_code_for_user", return_value=(user_info, tokens)), \
         patch.object(auth_router, "UserRepository", return_value=repo):
        resp = client.get("/auth/callback", params={"code": "abc"}, follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert "/app" in resp.headers["location"]
    assert "session=" in resp.headers.get("set-cookie", "")


def test_callback_failure_redirects_with_error(client):
    with patch.object(auth_router, "exchange_code_for_user", side_effect=RuntimeError("bad code")):
        resp = client.get("/auth/callback", params={"code": "bad"}, follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "error=auth_failed" in resp.headers["location"]


def test_status_authenticated(auth_client):
    resp = auth_client.get("/auth/status")
    assert resp.status_code == 200
    assert resp.json() == {
        "authenticated": True, "email": "test@gmail.com", "name": "Test User",
    }


def test_me_returns_profile(auth_client):
    resp = auth_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["google_id"] == "google_123"


def test_logout_clears_cookie(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"
