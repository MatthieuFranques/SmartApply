# app/routers/enrich.py

from fastapi import APIRouter, HTTPException
from typing import List
from dataclasses import asdict
import os
import json
import time

from app.models.enrich import EnrichRequest, EnrichResponse, EnrichSummary
from app.services.enrich.enrich_pipeline import enrich_company, summarize_context

router = APIRouter(prefix="/enrich", tags=["Enrich"])


# ─── Logique métier ──────────────────────────────────────────

def build_output_file(input_file: str) -> str:
    dir_ = os.path.dirname(input_file)
    return os.path.join(dir_, "enriched.json")


def run_enrich(input_file: str, output_file: str, limit: int = None) -> EnrichSummary:
    print(f"\n{'═'*55}")
    print(f"  🧬 ENRICHISSEMENT")
    print(f"{'═'*55}")
    print(f"  📂 Fichier entrée  : {input_file}")
    print(f"  📂 Fichier sortie  : {output_file}")
    print(f"  📂 Existe          : {os.path.exists(input_file)}")

    with open(input_file, encoding="utf-8") as f:
        rows = json.load(f)

    if limit:
        rows = rows[:limit]

    print(f"  📋 {len(rows)} entreprise(s) à traiter\n")

    results, errors = [], 0
    total = len(rows)

    for i, row in enumerate(rows, 1):
        nom = row.get("nom", "?")
        domaine = row.get("domaine", "?")
        print(f"  [{i}/{total}] 🔍 {nom} ({domaine})")

        ctx = enrich_company(row)
        results.append(asdict(ctx))

        if ctx.scrape_status != "ok":
            errors += 1
            print(f"      ⚠️  {ctx.scrape_status} : {ctx.scrape_error}")
        else:
            print(f"      ✅ {summarize_context(ctx)}")

        time.sleep(1.5)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n  📊 RÉSUMÉ")
    print(f"  Total    : {len(results)}")
    print(f"  Succès   : {len(results) - errors}")
    print(f"  Erreurs  : {errors}")
    print(f"  Offres   : {sum(1 for r in results if r.get('job_offers'))}")
    print(f"  Contacts : {sum(1 for r in results if r.get('contact_form'))}")

    return EnrichSummary(
        total        = len(results),
        success      = len(results) - errors,
        errors       = errors,
        with_offers  = sum(1 for r in results if r.get("job_offers")),
        with_contact = sum(1 for r in results if r.get("contact_form")),
        output_file  = output_file,
    )


# ─── Routes ──────────────────────────────────────────────────

@router.post("/start", response_model=EnrichResponse)
def start_enrich(request: EnrichRequest):
    """Lance l'enrichissement et retourne le résumé."""
    print(f"\n🚀 POST /enrich/start — fichier : {request.input_file}")

    if not os.path.exists(request.input_file):
        print(f"  ❌ Fichier introuvable : {request.input_file}")
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {request.input_file}")

    output_file = request.output_file or build_output_file(request.input_file)
    summary     = run_enrich(request.input_file, output_file, request.limit)

    return EnrichResponse(message="Enrichissement terminé ✅", summary=summary)


@router.get("/results", response_model=List[str])
def get_enrich_results(output_dir: str = "./results"):
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    if not files:
        raise HTTPException(status_code=404, detail="Aucun résultat disponible")

    return files