from app.db.mongo import get_db


def create_indexes() -> None:
    """
    À appeler une seule fois au démarrage de l'app dans main.py.
    Idempotent — MongoDB ignore si l'index existe déjà.
    """
    db = get_db()

    db["users"].create_index("google_id", unique=True)
    db["jobs"].create_index("user_id")
    db["jobs"].create_index([("user_id", 1), ("stage", 1)])
    db["cover_letters"].create_index("job_id")
    db["cover_letters"].create_index("user_id")
    db["applications"].create_index("user_id")
    db["applications"].create_index([("user_id", 1), ("thread_id", 1)], unique=True)

    # TTL index — MongoDB auto-deletes expired job search cache entries
    db["job_search_cache"].create_index("expires_at", expireAfterSeconds=0)

    # job_offers — persistent offer store, TTL 90 days from date_posted
    db["job_offers"].create_index([("user_id", 1), ("offer_id", 1)], unique=True)
    db["job_offers"].create_index("expires_at", expireAfterSeconds=0)