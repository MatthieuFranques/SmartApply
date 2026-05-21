from fastapi import APIRouter

from app.config import DEFAULT_USER_ID
from app.services.ingestor import (
    CV_DIR,
    CV_EXTENSIONS,
    LETTER_EXTENSIONS,
    LETTERS_DIR,
    ingest_inbox,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
def trigger_ingest(user_id: str = DEFAULT_USER_ID):
    """Ingère tous les fichiers présents dans data/inbox/cvs/ et data/inbox/letters/."""
    return ingest_inbox(user_id)


@router.get("/status")
def ingest_status():
    """Liste les fichiers en attente d'ingestion dans l'inbox."""
    cv_files = sorted(
        f.name for f in CV_DIR.iterdir()
        if CV_DIR.exists() and f.suffix.lower() in CV_EXTENSIONS
    ) if CV_DIR.exists() else []

    letter_files = sorted(
        f.name for f in LETTERS_DIR.iterdir()
        if LETTERS_DIR.exists() and f.suffix.lower() in LETTER_EXTENSIONS
    ) if LETTERS_DIR.exists() else []

    return {
        "inbox_cvs":     cv_files,
        "inbox_letters": letter_files,
        "total":         len(cv_files) + len(letter_files),
    }
