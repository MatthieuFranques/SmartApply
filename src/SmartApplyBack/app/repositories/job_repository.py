from datetime import datetime
from typing import Optional
from pymongo import ReturnDocument
from pymongo.collection import Collection

from app.models.job import Job
from app.db.mongo import get_db


class JobRepository:
    def __init__(self):
        self.col: Collection = get_db()["jobs"]

    # ── Écriture ─────────────────────────────────────────────

    def save_many(self, jobs: list[dict], user_id: str, stage: str) -> int:
        """
        Insère une liste de jobs bruts (dict depuis le scraping).
        Upsert sur (user_id + domaine) — évite les doublons si on re-scrape.
        Retourne le nombre de documents traités.
        """
        for job in jobs:
            self.col.update_one(
                {
                    "user_id": user_id,
                    "domaine": job["domaine"],   # clé métier unique
                },
                {
                    "$set": {
                        **job,
                        "user_id":    user_id,
                        "stage":      stage,
                        "status":     "active",
                        "updated_at": datetime.now(),
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(),
                    },
                },
                upsert=True,
            )
        return len(jobs)

    def update_stage(
        self,
        user_id: str,
        domaine: str,
        stage: str,
        status: str = "active",
        extra_fields: dict = {},
    ) -> Optional[Job]:
        """
        Fait avancer un job dans la pipeline.
        ex: filter → deep, deep → enriched, ou → eliminated.
        """
        doc = self.col.find_one_and_update(
            {"user_id": user_id, "domaine": domaine},
            {
                "$set": {
                    "stage":      stage,
                    "status":     status,
                    "updated_at": datetime.now(),
                    **extra_fields,             # prescore, deep_score, etc.
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return Job(**doc)

    # ── Lecture ───────────────────────────────────────────────

    def find_by_user(self, user_id: str) -> list[Job]:
        """Tous les jobs actifs d'un user, tous stages confondus."""
        docs = self.col.find({"user_id": user_id, "status": "active"})
        return [Job(**{**d, "_id": str(d["_id"])}) for d in docs]

    def find_by_stage(self, user_id: str, stage: str) -> list[Job]:
        """Jobs d'un user à un stage précis (ex: pour la route /filter)."""
        docs = self.col.find({
            "user_id": user_id,
            "stage":   stage,
            "status":  "active",
        })
        return [Job(**{**d, "_id": str(d["_id"])}) for d in docs]

    def find_eliminated(self, user_id: str, stage: str) -> list[Job]:
        """Jobs éliminés à un stage donné — équivalent filter_eliminated.json."""
        docs = self.col.find({
            "user_id": user_id,
            "stage":   stage,
            "status":  "eliminated",
        })
        return [Job(**{**d, "_id": str(d["_id"])}) for d in docs]

    def find_one(self, user_id: str, domaine: str) -> Optional[Job]:
        doc = self.col.find_one({"user_id": user_id, "domaine": domaine})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return Job(**doc)