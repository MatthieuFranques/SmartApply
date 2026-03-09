# app/routers/scraping.py

import json

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
import os

from app.services.scraping.scraping_main import run_scraping
from app.models.scraping import ScrapingRequest, ScrapingResponse

router = APIRouter(prefix="/scraping", tags=["Scraping"])

# ─── Routes ──────────────────────────────────────────────────
# curl -X POST http://localhost:8000/scraping/start \
#   -H "Content-Type: application/json" \
#   -d '{"cities": ["Toulouse"], "output_dir": "results"}'
@router.post("/start", response_model=ScrapingResponse)
def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scraping, request.cities, request.output_dir)
    return ScrapingResponse(
        message="Scraping lancé en arrière-plan",
        cities=request.cities,
        output_dir=request.output_dir
    )

@router.get("/results", response_model=List[str])
def get_results(output_dir: str = "./results"):
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Dossier results introuvable")
    
    files = [
        f for f in os.listdir(output_dir)
        if f.endswith(".json") and f.startswith("scraping_results_")
    ]

    if not files:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")
    
    return files


@router.get("/results/{city}", response_model=List[dict])
def get_results_by_city(city: str, output_dir: str = "./results"):
    filepath = os.path.join(output_dir, f"scraping_results_{city.lower()}.json")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Aucun résultat pour la ville : {city}")

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    return data