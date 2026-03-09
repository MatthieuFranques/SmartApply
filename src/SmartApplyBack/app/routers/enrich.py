# app/routers/enrich.py

from fastapi import APIRouter, HTTPException
from typing import List
import os
import json

from app.models.enrich import EnrichRequest, EnrichResponse, EnrichSummary
from app.services.enrich.enrich_main import run_enrich, find_deep_results, build_output_file

router = APIRouter(prefix="/enrich", tags=["Enrich"])


@router.post("/start", response_model=EnrichResponse)
def start_enrich(request: EnrichRequest):
    """
    Lance l'enrichissement depuis le deep_results auto-détecté.
    input_file optionnel — si absent, prend le deep_results le plus récent.
    """
    print(f"\n POST /enrich/start")

    try:
        input_file = request.input_file or find_deep_results(request.base_dir or "results")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not os.path.exists(input_file):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {input_file}")

    output_file = request.output_file or build_output_file(input_file)
    summary     = run_enrich(input_file, output_file, request.limit)

    return EnrichResponse(message="Enrichissement terminé ", summary=summary)


@router.get("/results", response_model=List[dict])
def get_enrich_results(output_dir: str = "./results"):
    filepath = os.path.join(output_dir, "enriched.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)