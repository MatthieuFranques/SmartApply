from app.db.mongo import get_db


def create_indexes() -> None:
    db = get_db()
    db["users"].create_index("google_id", unique=True)
