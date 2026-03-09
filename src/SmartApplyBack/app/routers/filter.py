# app/routers/filter.py

from fastapi import APIRouter, HTTPException
from typing import List
import os

from app.models.filter import FilterRequest, FilterResponse, FilterSummary
from app.services.filters.filters_main import run_pipeline

router = APIRouter(prefix="/filter", tags=["Filter"])


# curl -X POST http://localhost:8000/filter/start \
#   -H "Content-Type: application/json" \
#   -d '{"cities": ["Toulouse", "Brussels", "Namur"]}'
@router.post("/start", response_model=FilterResponse)
def start_filter(request: FilterRequest):
    """Lance le pipeline complet de filtrage (préfiltre + deep filter)."""
    result = run_pipeline(
        cities         = request.cities,
        base_dir       = request.base_dir,
        min_prescore   = request.min_prescore,
        min_deep_score = request.min_deep_score,
        concurrency    = request.concurrency,
        skip_deep      = request.skip_deep,
    )

    if not result["pre_kept"]:
        raise HTTPException(status_code=422, detail="Aucune entreprise n'a passé le préfiltrage")

    return FilterResponse(
        message="Pipeline terminé",
        summary=FilterSummary(
            cities     = request.cities,
            output_dir = request.base_dir,
            pre_kept   = len(result["pre_kept"]),
            deep_kept  = len(result["deep_kept"]),
            paths      = result["paths"],
        )
    )


@router.get("/results", response_model=List[str])
def get_filter_results(output_dir: str = "./results"):
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    if not files:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")

    return files