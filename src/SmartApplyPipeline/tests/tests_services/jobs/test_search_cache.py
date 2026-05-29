"""Unit tests for the 12h job-search cache (key derivation + TTL logic)."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.services.jobs import search_cache


def test_cache_key_is_normalized_and_stable():
    k1 = search_cache._cache_key("Python", "France", 30)
    k2 = search_cache._cache_key("  python ", "  france ", 30)
    assert k1 == k2  # case + whitespace insensitive
    assert search_cache._cache_key("python", "France", 7) != k1  # days matter


def test_get_cached_miss_returns_none():
    db = MagicMock()
    db.__getitem__.return_value.find_one.return_value = None
    with patch.object(search_cache, "get_db", return_value=db):
        assert search_cache.get_cached("python", "France", 30) is None


def test_get_cached_fresh_returns_results():
    db = MagicMock()
    db.__getitem__.return_value.find_one.return_value = {
        "results": [{"title": "Dev"}],
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=5),
    }
    with patch.object(search_cache, "get_db", return_value=db):
        out = search_cache.get_cached("python", "France", 30)
    assert out == [{"title": "Dev"}]


def test_get_cached_expired_returns_none():
    db = MagicMock()
    db.__getitem__.return_value.find_one.return_value = {
        "results": [{"title": "Dev"}],
        "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    with patch.object(search_cache, "get_db", return_value=db):
        assert search_cache.get_cached("python", "France", 30) is None


def test_set_cached_upserts():
    collection = MagicMock()
    db = MagicMock()
    db.__getitem__.return_value = collection
    with patch.object(search_cache, "get_db", return_value=db):
        search_cache.set_cached("python", "France", 30, [{"title": "Dev"}])
    collection.replace_one.assert_called_once()
    _, kwargs = collection.replace_one.call_args
    assert kwargs.get("upsert") is True
