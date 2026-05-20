import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.user import User


FAKE_DOC = {
    "_id": "6600000000000000000000aa",
    "google_id": "gid_test",
    "email": "repo@test.com",
    "name": "Repo User",
    "picture": "https://pic.url/img.jpg",
    "access_token": "acc",
    "refresh_token": "ref",
    "token_expiry": datetime(2030, 1, 1),
    "scopes": ["gmail.readonly"],
    "created_at": datetime(2024, 1, 1),
    "updated_at": datetime(2024, 1, 1),
}


@pytest.fixture
def mock_col():
    return MagicMock()


@pytest.fixture
def repo(mock_col):
    from app.repositories.user_repository import UserRepository
    with patch("app.repositories.user_repository.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col
        mock_get_db.return_value = mock_db
        yield UserRepository()


def test_upsert_returns_user_instance(repo, mock_col):
    mock_col.find_one_and_update.return_value = dict(FAKE_DOC)
    user = repo.upsert(
        google_id="gid_test",
        email="repo@test.com",
        name="Repo User",
        picture="https://pic.url/img.jpg",
        access_token="acc",
        refresh_token="ref",
        token_expiry=datetime(2030, 1, 1),
        scopes=["gmail.readonly"],
    )
    assert isinstance(user, User)
    assert user.google_id == "gid_test"
    assert user.email == "repo@test.com"


def test_upsert_filters_by_google_id(repo, mock_col):
    mock_col.find_one_and_update.return_value = dict(FAKE_DOC)
    repo.upsert("gid_test", "repo@test.com", "Repo User", "", "acc", "ref", datetime(2030, 1, 1), [])
    call_filter = mock_col.find_one_and_update.call_args[0][0]
    assert call_filter == {"google_id": "gid_test"}


def test_upsert_converts_objectid_to_str(repo, mock_col):
    mock_col.find_one_and_update.return_value = dict(FAKE_DOC)
    user = repo.upsert("gid_test", "repo@test.com", "Repo User", "", "acc", "ref", datetime(2030, 1, 1), [])
    assert isinstance(user.id, str)


def test_find_by_google_id_found(repo, mock_col):
    mock_col.find_one.return_value = dict(FAKE_DOC)
    user = repo.find_by_google_id("gid_test")
    assert user is not None
    assert user.google_id == "gid_test"
    assert user.email == "repo@test.com"


def test_find_by_google_id_not_found_returns_none(repo, mock_col):
    mock_col.find_one.return_value = None
    assert repo.find_by_google_id("nonexistent") is None


def test_find_by_google_id_queries_correct_field(repo, mock_col):
    mock_col.find_one.return_value = None
    repo.find_by_google_id("gid_test")
    mock_col.find_one.assert_called_once_with({"google_id": "gid_test"})
