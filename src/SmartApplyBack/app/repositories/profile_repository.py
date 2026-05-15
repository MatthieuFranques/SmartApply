from app.db.mongo import get_db

DEFAULT_PROFILE: dict = {
    "prenom_nom":    "",
    "email":         "",
    "telephone":     "",
    "ville":         "",
    "portfolio":     "",
    "github":        "",
    "diplome":       "",
    "ecole":         "",
    "annee":         "",
    "experiences":   "",
    "projet_phare":  "",
    "competences":   "",
    "soft_skills":   "",
    "recherche":     "",
    "reference_letter": "",
    "cv_text":       "",
}


class UserProfileRepository:
    def __init__(self) -> None:
        self._col = get_db()["profiles"]

    def get(self, user_id: str) -> dict:
        doc = self._col.find_one({"user_id": user_id}, {"_id": 0, "user_id": 0})
        if not doc:
            return dict(DEFAULT_PROFILE)
        return {**DEFAULT_PROFILE, **doc}

    def upsert(self, user_id: str, data: dict) -> None:
        clean = {k: v for k, v in data.items() if k in DEFAULT_PROFILE}
        self._col.update_one(
            {"user_id": user_id},
            {"$set": clean},
            upsert=True,
        )
