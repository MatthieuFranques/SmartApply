import hashlib
import os
from datetime import datetime, timezone, timedelta

from app.db.mongo import get_db

_CACHE_TTL_HOURS = int(os.getenv("JOB_CACHE_TTL_HOURS", "12"))
_COLLECTION      = "job_search_cache"


def _cache_key(keywords: str, location: str, days: int) -> str:
    raw = f"{keywords.lower().strip()}|{location.lower().strip()}|{days}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(keywords: str, location: str, days: int) -> list[dict] | None:
    db  = get_db()
    key = _cache_key(keywords, location, days)
    doc = db[_COLLECTION].find_one({"_id": key})

    if doc is None:
        return None

    if datetime.now(timezone.utc) > doc["expires_at"].replace(tzinfo=timezone.utc):
        return None

    return doc["results"]


def set_cached(keywords: str, location: str, days: int, results: list[dict]) -> None:
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
