import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.services.auth.dependency import get_current_user, AuthUser


MOCK_USER = {
    "google_id": "google_123",
    "email": "test@gmail.com",
    "name": "Test User",
    "picture": None,
}


def _mock_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


@pytest.mark.asyncio
async def test_get_current_user_success(monkeypatch):
    """Valid session cookie → Gmail service returns 200 with user data."""
    mock_get = AsyncMock(return_value=_mock_response(200, MOCK_USER))

    with patch("app.services.auth.dependency.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=mock_get)
        )
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_current_user(session="valid_token")

    assert isinstance(result, AuthUser)
    assert result.google_id == "google_123"
    assert result.email == "test@gmail.com"


@pytest.mark.asyncio
async def test_get_current_user_no_cookie():
    """Missing session cookie → 401."""
    with pytest.raises(HTTPException) as exc:
        await get_current_user(session=None)

    assert exc.value.status_code == 401
    assert "Non authentifié" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_invalid_session(monkeypatch):
    """Gmail service returns 401 → propagate 401."""
    mock_get = AsyncMock(return_value=_mock_response(401))

    with patch("app.services.auth.dependency.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=mock_get)
        )
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(HTTPException) as exc:
            await get_current_user(session="expired_token")

    assert exc.value.status_code == 401
    assert "Session invalide" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_service_unavailable(monkeypatch):
    """Gmail service unreachable → 503."""
    mock_get = AsyncMock(side_effect=httpx.RequestError("timeout"))

    with patch("app.services.auth.dependency.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=mock_get)
        )
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(HTTPException) as exc:
            await get_current_user(session="any_token")

    assert exc.value.status_code == 503
    assert "unavailable" in exc.value.detail
