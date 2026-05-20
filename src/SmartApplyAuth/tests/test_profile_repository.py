import pytest
from unittest.mock import MagicMock, patch

from app.repositories.profile_repository import DEFAULT_PROFILE


@pytest.fixture
def mock_col():
    return MagicMock()


@pytest.fixture
def repo(mock_col):
    from app.repositories.profile_repository import UserProfileRepository
    with patch("app.repositories.profile_repository.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col
        mock_get_db.return_value = mock_db
        yield UserProfileRepository()


def test_get_returns_defaults_when_no_profile(repo, mock_col):
    mock_col.find_one.return_value = None
    result = repo.get("gid_123")
    assert result == DEFAULT_PROFILE


def test_get_merges_stored_data_with_defaults(repo, mock_col):
    mock_col.find_one.return_value = {"prenom_nom": "John Doe", "titre": "Engineer"}
    result = repo.get("gid_123")
    assert result["prenom_nom"] == "John Doe"
    assert result["titre"] == "Engineer"
    assert "email" in result


def test_get_all_default_keys_present(repo, mock_col):
    mock_col.find_one.return_value = {"prenom_nom": "Jane"}
    result = repo.get("gid_123")
    assert set(result.keys()) == set(DEFAULT_PROFILE.keys())


def test_upsert_saves_valid_keys(repo, mock_col):
    repo.upsert("gid_123", {"prenom_nom": "Jane Doe", "titre": "Dev"})
    call_args = mock_col.update_one.call_args
    update_doc = call_args[0][1]["$set"]
    assert "prenom_nom" in update_doc
    assert "titre" in update_doc


def test_upsert_ignores_unknown_keys(repo, mock_col):
    repo.upsert("gid_123", {"prenom_nom": "Jane", "hacker_field": "injected"})
    call_args = mock_col.update_one.call_args
    update_doc = call_args[0][1]["$set"]
    assert "hacker_field" not in update_doc
    assert "prenom_nom" in update_doc


def test_upsert_filters_by_user_id(repo, mock_col):
    repo.upsert("gid_abc", {"prenom_nom": "Test"})
    call_filter = mock_col.update_one.call_args[0][0]
    assert call_filter == {"user_id": "gid_abc"}
