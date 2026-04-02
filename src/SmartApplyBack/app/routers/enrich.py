from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.enrich import EnrichRequest, EnrichResponse, EnrichSummary
from app.models.user import User
from app.services.enrich.enrich_main import run_enrich
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user

router = APIRouter(prefix="/enrich", tags=["Enrich"])


@router.post("/start", response_model=EnrichResponse)
def start_enrich(
    request: EnrichRequest,
    current_user: User = Depends(get_current_user),
):
    repo = JobRepository()

    # Récupère les jobs deep depuis la DB au lieu de lire deep_results.json
    jobs = repo.find_by_stage(current_user.google_id, stage="deep")
    if not jobs:
        raise HTTPException(
            status_code=404,
            detail="Aucun job à enrichir — lancez d'abord /filter/start"
        )

    enriched_jobs = run_enrich(
        jobs  = [job.model_dump() for job in jobs],   # données, pas fichier
        limit = request.limit,
    )

    # Mise à jour en DB avec les données enrichies
    for job in enriched_jobs:
        repo.update_stage(
            user_id      = current_user.google_id,
            domaine      = job["domaine"],
            stage        = "enriched",
            extra_fields = {
                "description":       job.get("description"),
                "about_text":        job.get("about_text"),
                "tech_keywords":     job.get("tech_keywords", []),
                "job_keywords":      job.get("job_keywords", []),
                "job_titles_found":  job.get("job_titles_found", []),
                "key_phrases":       job.get("key_phrases", []),
                "company_size_hint": job.get("company_size_hint"),
                "is_recruiting":     job.get("is_recruiting"),
                "job_offers":        job.get("job_offers", []),
                "contact_form":      job.get("contact_form"),
                "scrape_status":     job.get("scrape_status"),
                "scrape_error":      job.get("scrape_error"),
            },
        )

    return EnrichResponse(
        message="Enrichissement terminé ✅",
        summary=EnrichSummary(enriched=len(enriched_jobs)),
    )


@router.get("/results", response_model=List[dict])
def get_enrich_results(
    current_user: User = Depends(get_current_user),
):
    jobs = JobRepository().find_by_stage(current_user.google_id, stage="enriched")
    if not jobs:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")
    return [job.model_dump(by_alias=False) for job in jobs]