"""Unit tests for the Google OAuth2 auth flow (URL build + code exchange)."""

import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

from app.services.auth import google_oauth


def test_get_auth_url_contains_expected_params():
    url = google_oauth.get_auth_url()
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert query["response_type"] == ["code"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    # All requested scopes are present, space-joined
    assert set(query["scope"][0].split()) == set(google_oauth.SCOPES)


def _resp(json_data: dict) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


def test_exchange_code_for_user_returns_user_and_tokens():
    token_payload = {
        "access_token": "ya29.token",
        "refresh_token": "1//refresh",
        "expires_in": 3600,
        "scope": "openid email profile",
    }
    user_payload = {"sub": "google_123", "email": "test@gmail.com", "name": "Test"}

    with patch.object(google_oauth, "http_requests") as mock_http:
        mock_http.post.return_value = _resp(token_payload)
        mock_http.get.return_value = _resp(user_payload)

        user_info, tokens = google_oauth.exchange_code_for_user("auth_code_123")

    assert user_info == user_payload
    assert tokens["access_token"] == "ya29.token"
    assert tokens["refresh_token"] == "1//refresh"
    assert tokens["scopes"] == ["openid", "email", "profile"]
    # Bearer header carries the freshly obtained access token
    _, kwargs = mock_http.get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer ya29.token"


def test_exchange_code_propagates_http_error():
    """A 4xx/5xx on the token endpoint bubbles up via raise_for_status."""
    bad = MagicMock()
    bad.raise_for_status.side_effect = RuntimeError("400 Bad Request")

    with patch.object(google_oauth, "http_requests") as mock_http:
        mock_http.post.return_value = bad
        with pytest.raises(RuntimeError):
            google_oauth.exchange_code_for_user("bad_code")
