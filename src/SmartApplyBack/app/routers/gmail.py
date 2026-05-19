import os
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.gmail.gmail import fetch_emails_by_label, create_gmail_draft
from app.services.generate_letter.generate_letter_generator import generate_letter
from app.services.auth.dependency import get_current_user
from app.repositories.job_repository import JobRepository
from app.models.gmail import GmailMessage, DraftRequest, DraftResponse
from app.models.user import User

router = APIRouter(prefix="/gmail", tags=["Gmail"])


@router.get("/messages", response_model=list[GmailMessage])
def get_messages(
    label: str = Query(default=os.getenv("GMAIL_LABEL", "Candidatures")),
    current_user: User = Depends(get_current_user),
):
    try:
        return fetch_emails_by_label(label, current_user.access_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft", response_model=DraftResponse)
def create_draft(
    body: DraftRequest,
    current_user: User = Depends(get_current_user),
):
    repo = JobRepository()
    job  = repo.find_one(current_user.google_id, body.domaine)
    if not job:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    company = job.model_dump(mode="json")

    try:
        letter_text = generate_letter(company, body.model, user_id=current_user.google_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG indisponible : {e}")

    contact_form = company.get("contact_form") or {}
    to           = contact_form.get("email_found", "")

    job_offers = company.get("job_offers") or []
    if job_offers:
        first_offer = job_offers[0].get("title", "")
        subject     = f"Candidature — {first_offer} — {company['nom']}"
    else:
        subject = f"Candidature spontanée — {company['nom']}"

    try:
        result = create_gmail_draft(
            access_token = current_user.access_token,
            subject      = subject,
            body         = letter_text,
            to           = to,
        )
    except Exception as e:
        raise HTTPException(
            status_code=403,
            detail="Impossible de créer le brouillon. Re-authentifie-toi pour activer gmail.compose.",
        )

    return DraftResponse(
        draft_id  = result["draft_id"],
        draft_url = result["draft_url"],
        to        = to,
        subject   = subject,
    )