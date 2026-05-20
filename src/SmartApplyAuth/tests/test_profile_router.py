import pytest
from unittest.mock import MagicMock, patch

from app.repositories.profile_repository import DEFAULT_PROFILE

FULL_PROFILE = {**DEFAULT_PROFILE, "prenom_nom": "Test User", "cv_text": "should_be_stripped"}


def test_get_profile_strips_cv_text(client):
    with patch("app.routers.profile.UserProfileRepository") as MockRepo:
        MockRepo.return_value.get.return_value = dict(FULL_PROFILE)
        response = client.get("/profile")
    assert response.status_code == 200
    data = response.json()
    assert "cv_text" not in data
    assert data["prenom_nom"] == "Test User"


def test_get_profile_all_default_keys_present(client):
    with patch("app.routers.profile.UserProfileRepository") as MockRepo:
        MockRepo.return_value.get.return_value = dict(DEFAULT_PROFILE)
        response = client.get("/profile")
    data = response.json()
    expected_keys = {k for k in DEFAULT_PROFILE if k != "cv_text"}
    assert expected_keys == set(data.keys())


def test_get_profile_unauthenticated_returns_401(unauth_client):
    response = unauth_client.get("/profile")
    assert response.status_code == 401


def test_update_profile_returns_ok(client):
    with patch("app.routers.profile.UserProfileRepository") as MockRepo:
        MockRepo.return_value.upsert.return_value = None
        response = client.put("/profile", json={"prenom_nom": "New Name", "titre": "Dev"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_update_profile_calls_upsert_with_user_id(client, mock_user):
    with patch("app.routers.profile.UserProfileRepository") as MockRepo:
        MockRepo.return_value.upsert.return_value = None
        client.put("/profile", json={"prenom_nom": "Jane"})
        MockRepo.return_value.upsert.assert_called_once()
        call_user_id = MockRepo.return_value.upsert.call_args[0][0]
        assert call_user_id == mock_user.google_id


def test_update_profile_unauthenticated_returns_401(unauth_client):
    response = unauth_client.put("/profile", json={"prenom_nom": "Jane"})
    assert response.status_code == 401


def test_get_defaults_excludes_cv_text_and_reference_letter(client):
    response = client.get("/profile/defaults")
    assert response.status_code == 200
    data = response.json()
    assert "cv_text" not in data
    assert "reference_letter" not in data
    assert "prenom_nom" in data


def test_get_defaults_no_auth_required(unauth_client):
    response = unauth_client.get("/profile/defaults")
    assert response.status_code == 200
