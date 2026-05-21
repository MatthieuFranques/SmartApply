from app.db.mongo import get_db


def create_indexes() -> None:
    db = get_db()
    db["users"].create_index("google_id", unique=True)
    db["applications"].create_index("user_id")
    db["applications"].create_index([("user_id", 1), ("thread_id", 1)], unique=True)
