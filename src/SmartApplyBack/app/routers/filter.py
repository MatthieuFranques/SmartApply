# app/routers/filter.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
import os

from app.models.filter import FilterRequest, FilterResponse, FilterSummary
from app.services.filters.filters_main import run_prefilter, run_deep_filter, build_output_dir, build_paths

router = APIRouter(prefix="/filter", tags=["Filter"])


# ─── Routes ──────────────────────────────────────────────────

@router.post("/start", response_model=FilterResponse)
def start_filter(request: FilterRequest, background_tasks: BackgroundTasks):
    """
    Lance le pipeline complet de filtrage en arrière-plan.
    """
    if not os.path.exists(request.input_file):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {request.input_file}")

    def run():
        output_dir = build_output_dir(request.input_file, request.output_dir)
        paths      = build_paths(request.input_file, output_dir)

        pre_kept = run_prefilter(request.input_file, paths, request.min_prescore)
        if not pre_kept or request.skip_deep:
            return

        run_deep_filter(pre_kept, paths, request.min_deep_score, request.concurrency)

    background_tasks.add_task(run)

    return FilterResponse(message="Pipeline de filtrage lancé en arrière-plan")


@router.post("/start-sync", response_model=FilterResponse)
def start_filter_sync(request: FilterRequest):
    """
    Lance le pipeline complet de façon synchrone et retourne le résumé.
    """
    if not os.path.exists(request.input_file):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {request.input_file}")

    output_dir = build_output_dir(request.input_file, request.output_dir)
    paths      = build_paths(request.input_file, output_dir)

    pre_kept = run_prefilter(request.input_file, paths, request.min_prescore)
    if not pre_kept:
        raise HTTPException(status_code=422, detail="Aucune entreprise n'a passé le préfiltrage")

    deep_kept = [] if request.skip_deep else run_deep_filter(
        pre_kept, paths, request.min_deep_score, request.concurrency
    )

    return FilterResponse(
        message="Pipeline terminé",
        summary=FilterSummary(
            input_file=request.input_file,
            output_dir=output_dir,
            pre_kept=len(pre_kept),
            deep_kept=len(deep_kept),
            paths=paths,
        )
    )


@router.get("/results", response_model=List[str])
def get_filter_results(output_dir: str):
    """
    Retourne la liste des fichiers JSON de résultats dans un dossier.
    """
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    if not files:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")

    return files