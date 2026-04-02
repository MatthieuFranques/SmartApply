from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import List

from app.services.scraping.scraping_main import run_scraping
from app.models.scraping import ScrapingRequest, ScrapingResponse
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user

router = APIRouter(prefix="/scraping", tags=["Scraping"])


async def _scraping_task(cities: list[str], user_id: str) -> None:
    """Tâche background : scrape puis sauvegarde en DB."""
    results = run_scraping(cities)          # retourne list[dict] au lieu d'écrire un fichier
    JobRepository().save_many(results, user_id, stage="scraping")


@router.post("/start", response_model=ScrapingResponse)
def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(
        _scraping_task,
        request.cities,
        current_user.google_id,
    )
    return ScrapingResponse(
        message="Scraping lancé en arrière-plan 🚀",
        cities=request.cities,
    )


@router.get("/results", response_model=List[dict])
def get_results(
    current_user: User = Depends(get_current_user),
):
    """Retourne les résultats de scraping depuis MongoDB."""
    jobs = JobRepository().find_by_stage(current_user.google_id, stage="scraping")
    if not jobs:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")
    return [job.model_dump(by_alias=False) for job in jobs]