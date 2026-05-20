from app.db.mongo import get_db


def create_indexes() -> None:
    db = get_db()
    db["users"].create_index("google_id", unique=True)
    db["job_search_cache"].create_index("expires_at", expireAfterSeconds=0)
    db["job_offers"].create_index([("user_id", 1), ("offer_id", 1)], unique=True)
    db["job_offers"].create_index("expires_at", expireAfterSeconds=0)
