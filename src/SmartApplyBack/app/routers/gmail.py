import os
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.gmail.gmail import fetch_emails_by_label
from app.services.auth.dependency import get_current_user
from app.models.gmail import GmailMessage
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