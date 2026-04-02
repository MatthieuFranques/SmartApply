from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.filter import FilterRequest, FilterResponse, FilterSummary
from app.models.user import User
from app.services.filters.filters_main import run_pipeline
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user

router = APIRouter(prefix="/filter", tags=["Filter"])


@router.post("/start", response_model=FilterResponse)
def start_filter(
    request: FilterRequest,
    current_user: User = Depends(get_current_user),
):
    repo = JobRepository()

    # Récupère les jobs du stage précédent depuis la DB
    jobs = repo.find_by_stage(current_user.google_id, stage="scraping")
    if not jobs:
        raise HTTPException(status_code=404, detail="Aucun job à filtrer — lancez d'abord /scraping/start")

    result = run_pipeline(
        jobs           = [job.model_dump() for job in jobs],  # on passe les données, pas un fichier
        min_prescore   = request.min_prescore,
        min_deep_score = request.min_deep_score,
        concurrency    = request.concurrency,
        skip_deep      = request.skip_deep,
    )

    if not result["pre_kept"]:
        raise HTTPException(status_code=422, detail="Aucune entreprise n'a passé le préfiltrage")

    # Mise à jour du stage en DB
    for job in result["pre_kept"]:
        repo.update_stage(
            user_id      = current_user.google_id,
            domaine      = job["domaine"],
            stage        = "filtered",
            extra_fields = {"prescore": job.get("prescore")},
        )

    for job in result["pre_eliminated"]:
        repo.update_stage(
            user_id = current_user.google_id,
            domaine = job["domaine"],
            stage   = "scraping",
            status  = "eliminated",
        )

    for job in result["deep_kept"]:
        repo.update_stage(
            user_id      = current_user.google_id,
            domaine      = job["domaine"],
            stage        = "deep",
            extra_fields = {"deep_score": job.get("deep_score")},
        )

    for job in result["deep_eliminated"]:
        repo.update_stage(
            user_id = current_user.google_id,
            domaine = job["domaine"],
            stage   = "filtered",
            status  = "eliminated",
        )

    return FilterResponse(
        message="Pipeline terminé ✅",
        summary=FilterSummary(
            cities     = request.cities,
            pre_kept   = len(result["pre_kept"]),
            deep_kept  = len(result["deep_kept"]),
        )
    )


@router.get("/results", response_model=List[dict])
def get_filter_results(
    current_user: User = Depends(get_current_user),
):
    """Retourne les jobs ayant passé le filtre deep."""
    jobs = JobRepository().find_by_stage(current_user.google_id, stage="deep")
    if not jobs:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")
    return [job.model_dump(by_alias=False) for job in jobs]


@router.get("/eliminated", response_model=List[dict])
def get_eliminated(
    stage: str = "scraping",
    current_user: User = Depends(get_current_user),
):
    """Retourne les jobs éliminés — remplace filter_eliminated.json et deep_eliminated.json."""
    jobs = JobRepository().find_eliminated(current_user.google_id, stage=stage)
    if not jobs:
        raise HTTPException(status_code=404, detail="Aucun éliminé à ce stage")
    return [job.model_dump(by_alias=False) for job in jobs]