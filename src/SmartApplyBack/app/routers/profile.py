from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.repositories.profile_repository import UserProfileRepository, DEFAULT_PROFILE

router = APIRouter(prefix="/profile", tags=["Profile"])


class UserProfileBody(BaseModel):
    prenom_nom:       str = ""
    titre:            str = ""
    email:            str = ""
    telephone:        str = ""
    ville:            str = ""
    portfolio:        str = ""
    github:           str = ""
    diplome:          str = ""
    ecole:            str = ""
    annee:            str = ""
    experiences:      str = ""
    projet_phare:     str = ""
    competences:      str = ""
    soft_skills:      str = ""
    recherche:        str = ""
    reference_letter: str = ""


@router.get("")
def get_profile(current_user: User = Depends(get_current_user)) -> dict:
    repo = UserProfileRepository()
    profile = repo.get(current_user.google_id)
    profile.pop("cv_text", None)
    return profile


@router.put("")
def update_profile(
    body: UserProfileBody,
    current_user: User = Depends(get_current_user),
) -> dict:
    repo = UserProfileRepository()
    repo.upsert(current_user.google_id, body.model_dump())
    return {"ok": True}


@router.get("/defaults")
def get_defaults() -> dict:
    return {k: v for k, v in DEFAULT_PROFILE.items() if k not in ("cv_text", "reference_letter")}
