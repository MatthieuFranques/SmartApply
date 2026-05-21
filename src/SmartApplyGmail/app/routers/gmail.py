import os
import httpx
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.gmail.gmail import fetch_emails_by_label, create_gmail_draft
from app.services.auth.dependency import get_current_user
from app.repositories.job_repository import JobRepository
from app.models.gmail import GmailMessage, DraftRequest, DraftResponse
from app.models.user import User

_RAG_URL     = os.getenv("RAG_URL")
_RAG_TIMEOUT = float(os.getenv("RAG_TIMEOUT", "120"))


def _determine_mode(company: dict) -> str:
    if company.get("job_offers"):
        return "letter"
    if company.get("contact_form") and not company.get("job_offers"):
        return "contact"
    return "letter"


def _call_rag(endpoint: str, payload: dict) -> dict | str:
    resp = httpx.post(
        f"{_RAG_URL}{endpoint}",
        json=payload,
        timeout=_RAG_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()

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
    mode = _determine_mode(company)

    contact_form = company.get("contact_form") or {}
    to           = contact_form.get("email_found", "")

    try:
        if mode == "contact":
            contact_data = _call_rag("/generate/contact", {
                "company": company, "profile": {}, "model": body.model, "user_id": current_user.google_id,
            })
            letter_text = contact_data.get("message") or contact_data.get("raw_response") or str(contact_data)
        else:
            result_data = _call_rag("/generate/letter", {
                "company": company, "profile": {}, "model": body.model,
                "reference_letter": "", "user_id": current_user.google_id,
            })
            letter_text = result_data["letter"]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG indisponible : {e}")

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