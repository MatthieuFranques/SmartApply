"""
job_offer_repository.py
-----------------------
Persistent storage for external job offers (JSearch + Adzuna).
One document per offer per user. TTL = 90 days from date_posted (or stored_at).
MongoDB TTL index on `expires_at` handles auto-cleanup.
Each offer stores the search context (keywords + location) for grouping.
"""

from datetime import datetime, timezone, timedelta

from app.db.mongo import get_db

_COLLECTION = "job_offers"
_TTL_DAYS   = 90


def _expires_at(date_posted: str, fallback: datetime) -> datetime:
    if date_posted:
        try:
            posted = datetime.fromisoformat(date_posted).replace(tzinfo=timezone.utc)
            return posted + timedelta(days=_TTL_DAYS)
        except ValueError:
            pass
    return fallback + timedelta(days=_TTL_DAYS)


def upsert_offers(user_id: str, offers: list[dict], keywords: str = "", location: str = "") -> None:
    """Upsert a batch of offers, tagging each with its search context."""
    db  = get_db()
    now = datetime.now(timezone.utc)

    for offer in offers:
        db[_COLLECTION].update_one(
            {"offer_id": offer["id"], "user_id": user_id},
            {"$set": {
                **offer,
                "offer_id":        offer["id"],
                "user_id":         user_id,
                "search_keywords": keywords.lower().strip(),
                "search_location": location.lower().strip(),
                "stored_at":       now,
                "expires_at":      _expires_at(offer.get("date_posted", ""), now),
            }},
            upsert=True,
        )


_EXCLUDE = {"_id": 0, "user_id": 0, "offer_id": 0, "expires_at": 0, "stored_at": 0}


def find_offers(user_id: str, keywords: str = "", location: str = "") -> list[dict]:
    """Return stored offers for a user, optionally filtered by search context."""
    db    = get_db()
    query: dict = {"user_id": user_id}
    if keywords:
        query["search_keywords"] = keywords.lower().strip()
    if location:
        query["search_location"] = location.lower().strip()

    return list(db[_COLLECTION].find(query, _EXCLUDE))


def find_offers_grouped(user_id: str) -> list[dict]:
    """
    Return stored offers grouped by search query.
    Each group: { keywords, location, count, offers[] }
    Sorted by most recent stored_at desc.
    """
    db   = get_db()
    docs = list(db[_COLLECTION].find(
        {"user_id": user_id},
        {"_id": 0, "user_id": 0, "offer_id": 0, "expires_at": 0},
    ).sort("stored_at", -1))

    groups: dict[str, dict] = {}
    for doc in docs:
        kw  = doc.get("search_keywords", "")
        loc = doc.get("search_location", "")
        key = f"{kw}||{loc}"

        if key not in groups:
            groups[key] = {
                "keywords": kw,
                "location": loc,
                "offers":   [],
            }

        _internal = {"search_keywords", "search_location", "stored_at"}
        offer = {k: v for k, v in doc.items() if k not in _internal}
        groups[key]["offers"].append(offer)

    result = list(groups.values())
    for g in result:
        g["count"] = len(g["offers"])

    return result


def count_offers(user_id: str) -> int:
    return get_db()[_COLLECTION].count_documents({"user_id": user_id})
