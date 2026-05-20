import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


def test_login_redirects_to_google(client):
    with patch("app.routers.auth.get_auth_url", return_value="https://accounts.google.com/o/oauth2/v2/auth?mock=1"):
        response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "accounts.google.com" in response.headers["location"]


def test_status_authenticated(client):
    response = client.get("/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_status_unauthenticated_returns_401(unauth_client):
    response = unauth_client.get("/auth/status")
    assert response.status_code == 401


def test_logout_returns_200(client):
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out"


def test_logout_clears_session_cookie(client):
    response = client.post("/auth/logout")
    set_cookie = response.headers.get("set-cookie", "")
    assert "session" in set_cookie


def test_callback_success_sets_session_cookie(client):
    mock_user_info = {
        "sub": "gid_new",
        "email": "new@example.com",
        "name": "New User",
        "picture": "https://pic.url",
    }
    mock_tokens = {
        "access_token": "acc",
        "refresh_token": "ref",
        "expiry": datetime(2030, 1, 1),
        "scopes": ["gmail.readonly"],
    }
    mock_repo_user = MagicMock()
    mock_repo_user.google_id = "gid_new"

    with patch("app.routers.auth.exchange_code_for_user", return_value=(mock_user_info, mock_tokens)), \
         patch("app.routers.auth.UserRepository") as MockRepo:
        MockRepo.return_value.upsert.return_value = mock_repo_user
        response = client.get("/auth/callback?code=valid_code", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert "session" in response.headers.get("set-cookie", "")


def test_callback_failure_redirects_with_error(client):
    with patch("app.routers.auth.exchange_code_for_user", side_effect=Exception("OAuth error")):
        response = client.get("/auth/callback?code=bad_code", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "error=auth_failed" in response.headers["location"]


def test_callback_missing_code_returns_422(client):
    response = client.get("/auth/callback")
    assert response.status_code == 422
