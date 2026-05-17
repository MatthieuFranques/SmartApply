"""
search_cache.py
---------------
MongoDB-backed cache for external job search results (JSearch + Adzuna).
Cache is global (job listings are public data — no per-user isolation needed).
TTL is enforced by a MongoDB TTL index on `expires_at` (auto-delete).
"""

import hashlib
import os
from datetime import datetime, timezone, timedelta

from app.db.mongo import get_db

_CACHE_TTL_HOURS = int(os.getenv("JOB_CACHE_TTL_HOURS", "12"))
_COLLECTION      = "job_search_cache"


def _cache_key(keywords: str, location: str, days: int) -> str:
    raw = f"{keywords.lower().strip()}|{location.lower().strip()}|{days}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(keywords: str, location: str, days: int) -> list[dict] | None:
    """Return cached results if still valid, else None."""
    db  = get_db()
    key = _cache_key(keywords, location, days)
    doc = db[_COLLECTION].find_one({"_id": key})

    if doc is None:
        return None

    # Paranoia check — TTL index handles deletion but may lag a few seconds
    if datetime.now(timezone.utc) > doc["expires_at"].replace(tzinfo=timezone.utc):
        return None

    return doc["results"]


def set_cached(keywords: str, location: str, days: int, results: list[dict]) -> None:
    """Store results in cache with TTL."""
    db  = get_db()
    key = _cache_key(keywords, location, days)
    now = datetime.now(timezone.utc)

    db[_COLLECTION].replace_one(
        {"_id": key},
        {
            "_id":        key,
            "keywords":   keywords,
            "location":   location,
            "days":       days,
            "results":    results,
            "cached_at":  now,
            "expires_at": now + timedelta(hours=_CACHE_TTL_HOURS),
        },
        upsert=True,
    )
