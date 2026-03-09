# app/routers/scraping.py

import json
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
import os

from app.services.scraping.scraping_main import run_scraping
from app.models.scraping import ScrapingRequest, ScrapingResponse

router = APIRouter(prefix="/scraping", tags=["Scraping"])


@router.post("/start", response_model=ScrapingResponse)
def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scraping, request.cities, request.output_dir)
    return ScrapingResponse(
        message="Scraping lancé en arrière-plan ",
        cities=request.cities,
        output_dir=request.output_dir
    )


@router.get("/results", response_model=List[dict])
def get_results(output_dir: str = "./results"):
    """Retourne le contenu du fichier scraping_results.json."""
    filepath = os.path.join(output_dir, "scraping_results.json")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    return data