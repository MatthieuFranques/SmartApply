from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.repositories.profile_repository import UserProfileRepository, DEFAULT_PROFILE
from app.services.generate_letter.cv_parser import extract_pdf_text, parse_cv_profile, suggest_pipeline_config

router = APIRouter(prefix="/profile", tags=["Profile"])

OLLAMA_MODEL = "mistral"


class UserProfileBody(BaseModel):
    prenom_nom:       str = ""
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


@router.post("/cv")
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="PDF only")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    cv_text = extract_pdf_text(pdf_bytes)
    if not cv_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    profile_data = parse_cv_profile(cv_text, OLLAMA_MODEL)
    suggestion   = suggest_pipeline_config(profile_data, OLLAMA_MODEL)

    repo = UserProfileRepository()
    existing = repo.get(current_user.google_id)
    merged = {**existing, **{k: v for k, v in profile_data.items() if v}, "cv_text": cv_text}
    repo.upsert(current_user.google_id, merged)

    clean_profile = {k: merged[k] for k in DEFAULT_PROFILE if k != "cv_text"}
    return {"profile": clean_profile, "pipeline_suggestion": suggestion}


@router.get("/defaults")
def get_defaults() -> dict:
    return {k: v for k, v in DEFAULT_PROFILE.items() if k not in ("cv_text", "reference_letter")}
