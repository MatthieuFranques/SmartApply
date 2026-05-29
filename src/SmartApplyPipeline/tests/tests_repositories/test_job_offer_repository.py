"""Tests for job_offer_repository (Mongo mocked)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.repositories import job_offer_repository as jor


def _db_with(col):
    db = MagicMock()
    db.__getitem__.return_value = col
    return db


def test_expires_at_uses_posted_date():
    out = jor._expires_at("2025-01-01", datetime(2025, 6, 1, tzinfo=timezone.utc))
    assert out.year == 2025 and out.month == 4  # 2025-01-01 + 90 days


def test_expires_at_falls_back_on_bad_date():
    fallback = datetime(2025, 6, 1, tzinfo=timezone.utc)
    out = jor._expires_at("not-a-date", fallback)
    assert out > fallback


def test_upsert_offers_calls_update_per_offer():
    col = MagicMock()
    offers = [{"id": "a1", "date_posted": ""}, {"id": "a2", "date_posted": "2025-01-01"}]
    with patch.object(jor, "get_db", return_value=_db_with(col)):
        jor.upsert_offers("u1", offers, "python", "France")
    assert col.update_one.call_count == 2
    assert col.update_one.call_args_list[0].kwargs.get("upsert") is True


def test_find_offers_builds_query():
    col = MagicMock()
    col.find.return_value = [{"title": "Dev"}]
    with patch.object(jor, "get_db", return_value=_db_with(col)):
        out = jor.find_offers("u1", "python", "france")
    assert out == [{"title": "Dev"}]
    query = col.find.call_args[0][0]
    assert query["search_keywords"] == "python"
    assert query["search_location"] == "france"


def test_find_offers_grouped():
    col = MagicMock()
    cursor = MagicMock()
    cursor.sort.return_value = [
        {"search_keywords": "python", "search_location": "france", "title": "A", "stored_at": 1},
        {"search_keywords": "python", "search_location": "france", "title": "B", "stored_at": 2},
        {"search_keywords": "java", "search_location": "france", "title": "C", "stored_at": 3},
    ]
    col.find.return_value = cursor
    with patch.object(jor, "get_db", return_value=_db_with(col)):
        groups = jor.find_offers_grouped("u1")
    by_kw = {g["keywords"]: g for g in groups}
    assert by_kw["python"]["count"] == 2
    assert by_kw["java"]["count"] == 1
    # internal fields stripped from offers
    assert "search_keywords" not in by_kw["python"]["offers"][0]


def test_count_offers():
    col = MagicMock()
    col.count_documents.return_value = 5
    with patch.object(jor, "get_db", return_value=_db_with(col)):
        assert jor.count_offers("u1") == 5
