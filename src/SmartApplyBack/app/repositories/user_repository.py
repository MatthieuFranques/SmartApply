from datetime import datetime
from typing import Optional
from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection
import os

from app.models.user import User


class UserRepository:
    def __init__(self):
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client[os.getenv("MONGODB_DB", "jobpipeline")]
        self.col: Collection = db["users"]
        # Index unique sur google_id — une seule fois au démarrage
        self.col.create_index("google_id", unique=True)

    def upsert(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: str,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
        scopes: list[str],
    ) -> User:
        """Crée ou met à jour un user à chaque connexion."""
        doc = self.col.find_one_and_update(
            {"google_id": google_id},
            {
                "$set": {
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_expiry": token_expiry,
                    "scopes": scopes,
                    "updated_at": datetime.now(),
                },
                "$setOnInsert": {
                    "created_at": datetime.now(),
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        doc["_id"] = str(doc["_id"])   # ObjectId → str
        return User(**doc)

    def find_by_google_id(self, google_id: str) -> Optional[User]:
        doc = self.col.find_one({"google_id": google_id})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return User(**doc)