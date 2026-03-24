from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.job_applications import CandidatureItem, SyncResult
from app.services.job_applications.job_applications import (
    sync_candidatures,
    load_history,
    reset_history,
    get_last_sync,
)

router = APIRouter(prefix="/candidatures", tags=["Candidatures"])


# ── GET /candidatures ─────────────────────────────────────────
@router.get(
    "",
    response_model=list[CandidatureItem],
    summary="Lire l'historique local (sans appel Gmail)"
)
def get_candidatures(
    statut: Optional[str] = Query(default=None, description="Filtrer par statut"),
):
    """
    Retourne les candidatures depuis jobs_history.json.
    Aucun appel à l'API Gmail — lecture locale uniquement.
    """
    history = load_history()
    if statut:
        history = [c for c in history if c.get("statut", "").lower() == statut.lower()]
    return history


# ── POST /candidatures/sync ───────────────────────────────────
@router.post(
    "/sync",
    response_model=SyncResult,
    summary="Synchroniser Gmail → jobs_history.json"
)
def sync(force_full: bool = Query(default=False)):
    """
    Fetch les nouveaux mails Gmail depuis la dernière sync,
    parse et met à jour jobs_history.json.
    Si force_full=true : repart de zéro et refetch tout.
    """
    try:
        result = sync_candidatures(force_full=force_full)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /candidatures/status ──────────────────────────────────
@router.get(
    "/status",
    summary="Infos sur la dernière synchronisation"
)
def sync_status():
    """Retourne la date de la dernière sync et le nombre de candidatures en cache."""
    last_sync = get_last_sync()
    history   = load_history()
    return {
        "derniere_sync":    last_sync.isoformat() if last_sync else None,
        "total_en_cache":   len(history),
        "jamais_synchronise": last_sync is None,
    }


# ── DELETE /candidatures/reset ────────────────────────────────
@router.delete(
    "/reset",
    summary="Réinitialiser l'historique local"
)
def reset():
    """Supprime jobs_history.json et sync_meta.json pour repartir de zéro."""
    reset_history()
    return {"message": "Historique réinitialisé. Lance /candidatures/sync pour tout recharger."}