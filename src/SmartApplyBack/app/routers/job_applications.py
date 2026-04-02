from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.models.job_applications import CandidatureItem, SyncResult
from app.services.job_applications.job_applications import sync_candidatures
from app.repositories.application_repository import ApplicationRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User

router = APIRouter(prefix="/candidatures", tags=["Candidatures"])


def get_repo() -> ApplicationRepository:
    return ApplicationRepository()


@router.get("", response_model=list[dict])
def get_candidatures(
    statut: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    repo: ApplicationRepository = Depends(get_repo),
):
    history = repo.find_by_user(current_user.google_id)
    if statut:
        history = [c for c in history if c.get("statut", "").lower() == statut.lower()]
    return history


@router.post("/sync", response_model=SyncResult)
def sync(
    force_full: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    repo: ApplicationRepository = Depends(get_repo),
):
    try:
        return sync_candidatures(
            access_token = current_user.access_token,
            user_id      = current_user.google_id,
            repo         = repo,
            force_full   = force_full,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def sync_status(
    current_user: User = Depends(get_current_user),
    repo: ApplicationRepository = Depends(get_repo),
):
    last_sync = repo.get_last_sync(current_user.google_id)
    history   = repo.find_by_user(current_user.google_id)
    return {
        "derniere_sync":      last_sync.isoformat() if last_sync else None,
        "total_en_cache":     len(history),
        "jamais_synchronise": last_sync is None,
    }


@router.delete("/reset")
def reset(
    current_user: User = Depends(get_current_user),
    repo: ApplicationRepository = Depends(get_repo),
):
    repo.delete_by_user(current_user.google_id)
    return {"message": "Historique supprimé."}