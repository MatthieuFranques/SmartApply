from datetime import datetime, timezone
from typing import Optional
from pymongo.collection import Collection
from app.db.mongo import get_db


class ApplicationRepository:
    def __init__(self):
        self.col: Collection = get_db()["applications"]

    def find_by_user(self, user_id: str) -> list:
        return list(self.col.find({"user_id": user_id}))

    def save(self, item: dict) -> None:
        self.col.insert_one(item)

    def update_statut(
        self,
        user_id: str,
        thread_id: str,
        statut: str,
        date: str,
        ville: str,
    ) -> None:
        update = {"statut": statut, "date": date}
        if ville:
            update["ville"] = ville
        self.col.update_one(
            {"user_id": user_id, "thread_id": thread_id},
            {"$set": update},
        )

    def get_last_sync(self, user_id: str) -> Optional[datetime]:
        doc = self.col.find_one({"user_id": user_id, "_type": "sync_meta"})
        if not doc:
            return None
        return doc.get("last_sync")

    def set_last_sync(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        self.col.update_one(
            {"user_id": user_id, "_type": "sync_meta"},
            {"$set": {"last_sync": now}},
            upsert=True,
        )
        return now.isoformat()
    
    def delete_by_user(self, user_id: str) -> None: self.col.delete_many({"user_id": user_id})