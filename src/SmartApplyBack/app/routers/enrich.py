# app/routers/enrich.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
from dataclasses import asdict
import os
import json
import time

from app.models.enrich import EnrichRequest, EnrichResponse, EnrichSummary
from app.services.enrich.enrich_pipeline import enrich_company, summarize_context

router = APIRouter(prefix="/enrich", tags=["Enrich"])


# ─── Logique métier ──────────────────────────────────────────

def run_enrich(input_file: str, output_file: str, limit: int = None) -> EnrichSummary:
    with open(input_file, encoding="utf-8") as f:
        rows = json.load(f)

    if limit:
        rows = rows[:limit]

    results, errors = [], 0

    for row in rows:
        ctx = enrich_company(row)
        results.append(asdict(ctx))

        if ctx.scrape_status != "ok":
            errors += 1

        time.sleep(1.5)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return EnrichSummary(
        total        = len(results),
        success      = len(results) - errors,
        errors       = errors,
        with_offers  = sum(1 for r in results if r.get("job_offers")),
        with_contact = sum(1 for r in results if r.get("contact_form")),
        output_file  = output_file,
    )


def build_output_file(input_file: str) -> str:
    dir_ = os.path.dirname(input_file)
    return os.path.join(dir_, "enriched.json")


# ─── Routes ──────────────────────────────────────────────────

@router.post("/start", response_model=EnrichResponse)
def start_enrich(request: EnrichRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(request.input_file):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {request.input_file}")

    output_file = request.output_file or build_output_file(request.input_file)
    background_tasks.add_task(run_enrich, request.input_file, output_file, request.limit)

    return EnrichResponse(message=f"Enrichissement lancé en arrière-plan ✅ → {output_file}")


@router.post("/start-sync", response_model=EnrichResponse)
def start_enrich_sync(request: EnrichRequest):
    if not os.path.exists(request.input_file):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {request.input_file}")

    output_file = request.output_file or build_output_file(request.input_file)
    summary     = run_enrich(request.input_file, output_file, request.limit)

    return EnrichResponse(message="Enrichissement terminé ✅", summary=summary)


@router.get("/results", response_model=List[str])
def get_enrich_results(output_dir: str):
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    if not files:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")

    return files