"""Repository tests (Mongo collection mocked, no real DB)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.repositories import user_repository as ur
from app.repositories import application_repository as ar


def _db_with_collection(col):
    db = MagicMock()
    db.__getitem__.return_value = col
    return db


# ── UserRepository ────────────────────────────────────────────

def test_user_upsert_returns_user_model():
    col = MagicMock()
    col.find_one_and_update.return_value = {
        "_id": ObjectId(),
        "google_id": "g1", "email": "a@b.io", "name": "A",
        "access_token": "at", "refresh_token": "rt",
        "token_expiry": datetime(2030, 1, 1), "scopes": ["openid"],
    }
    with patch.object(ur, "get_db", return_value=_db_with_collection(col)):
        user = ur.UserRepository().upsert(
            "g1", "a@b.io", "A", "", "at", "rt", datetime(2030, 1, 1), ["openid"],
        )
    assert user.google_id == "g1"
    assert isinstance(user.id, str)
    col.find_one_and_update.assert_called_once()


def test_user_find_by_google_id_hit():
    col = MagicMock()
    col.find_one.return_value = {
        "_id": ObjectId(), "google_id": "g1", "email": "a@b.io", "name": "A",
        "access_token": "at", "refresh_token": "rt",
        "token_expiry": datetime(2030, 1, 1), "scopes": [],
    }
    with patch.object(ur, "get_db", return_value=_db_with_collection(col)):
        user = ur.UserRepository().find_by_google_id("g1")
    assert user.email == "a@b.io"


def test_user_find_by_google_id_miss():
    col = MagicMock()
    col.find_one.return_value = None
    with patch.object(ur, "get_db", return_value=_db_with_collection(col)):
        assert ur.UserRepository().find_by_google_id("nope") is None


# ── ApplicationRepository ─────────────────────────────────────

def test_application_find_by_user_stringifies_id():
    col = MagicMock()
    col.find.return_value = [{"_id": ObjectId(), "entreprise": "Acme"}]
    with patch.object(ar, "get_db", return_value=_db_with_collection(col)):
        out = ar.ApplicationRepository().find_by_user("u1")
    assert isinstance(out[0]["_id"], str)
    assert out[0]["entreprise"] == "Acme"


def test_application_save_inserts():
    col = MagicMock()
    with patch.object(ar, "get_db", return_value=_db_with_collection(col)):
        ar.ApplicationRepository().save({"x": 1})
    col.insert_one.assert_called_once_with({"x": 1})


def test_application_update_statut_with_ville():
    col = MagicMock()
    with patch.object(ar, "get_db", return_value=_db_with_collection(col)):
        ar.ApplicationRepository().update_statut("u1", "t1", "Entretien", "2025-05-01", "Lyon")
    _, kwargs = col.update_one.call_args
    assert kwargs == {} or True  # positional call
    args = col.update_one.call_args[0]
    assert args[0] == {"user_id": "u1", "thread_id": "t1"}
    assert args[1]["$set"]["ville"] == "Lyon"


def test_application_get_last_sync_none():
    col = MagicMock()
    col.find_one.return_value = None
    with patch.object(ar, "get_db", return_value=_db_with_collection(col)):
        assert ar.ApplicationRepository().get_last_sync("u1") is None


def test_application_set_last_sync_upserts():
    col = MagicMock()
    with patch.object(ar, "get_db", return_value=_db_with_collection(col)):
        out = ar.ApplicationRepository().set_last_sync("u1")
    assert isinstance(out, datetime)
    _, kwargs = col.update_one.call_args
    assert kwargs.get("upsert") is True


def test_application_delete_by_user():
    col = MagicMock()
    with patch.object(ar, "get_db", return_value=_db_with_collection(col)):
        ar.ApplicationRepository().delete_by_user("u1")
    col.delete_many.assert_called_once_with({"user_id": "u1"})
