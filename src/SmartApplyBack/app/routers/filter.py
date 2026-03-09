# app/routers/filter.py

from fastapi import APIRouter, HTTPException
from typing import List
import os
import json

from app.models.filter import FilterRequest, FilterResponse, FilterSummary
from app.services.filters.filters_main import run_pipeline

router = APIRouter(prefix="/filter", tags=["Filter"])


@router.post("/start", response_model=FilterResponse)
def start_filter(request: FilterRequest):
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
        message="Pipeline terminé ✅",
        summary=FilterSummary(
            cities     = request.cities,
            output_dir = request.base_dir,
            pre_kept   = len(result["pre_kept"]),
            deep_kept  = len(result["deep_kept"]),
            paths      = result["paths"],
        )
    )


@router.get("/results", response_model=List[dict])
def get_filter_results(output_dir: str = "./results"):
    """Retourne le contenu de deep_results.json."""
    filepath = os.path.join(output_dir, "deep_results.json")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")

    with open(filepath, encoding="utf-8") as f:
        return json.load(f)