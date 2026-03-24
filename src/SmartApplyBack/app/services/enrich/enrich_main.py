"""
enrich_main.py
--------------
Logique métier partagée entre le router FastAPI et le CLI.
"""

import os
import json
import time
from dataclasses import asdict

from app.models.enrich import EnrichSummary
from app.services.enrich.enrich_pipeline import enrich_company, summarize_context


# ─── Chemins ─────────────────────────────────────────────────

def find_deep_results(base_dir: str = "results") -> str:
    filepath = os.path.join(base_dir, "deep_results.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable : '{filepath}'")
    print(f"  📂 deep_results : {filepath}")
    return filepath


def build_output_file(base_dir: str = "results") -> str:
    return os.path.join(base_dir, "enriched.json")


# ─── Pipeline d'enrichissement ───────────────────────────────

def run_enrich(input_file: str, output_file: str, limit: int = None) -> EnrichSummary:
    print(f"\n{'═'*55}")
    print(f"  🧬 ENRICHISSEMENT")
    print(f"{'═'*55}")
    print(f"  📂 Entrée : {input_file}")
    print(f"  📂 Sortie : {output_file}")

    with open(input_file, encoding="utf-8") as f:
        rows = json.load(f)

    if limit:
        rows = rows[:limit]

    print(f"  📋 {len(rows)} entreprise(s) à traiter\n")

    results, errors = [], 0
    total = len(rows)

    for i, row in enumerate(rows, 1):
        print(f"  [{i}/{total}] 🔍 {row.get('nom', '?')} ({row.get('domaine', '?')})")

        ctx = enrich_company(row)
        results.append(asdict(ctx))

        if ctx.scrape_status != "ok":
            errors += 1
            print(f"      ⚠️  {ctx.scrape_status} : {ctx.scrape_error}")
        else:
            print(f"      ✅ {summarize_context(ctx)}")

        time.sleep(1.5)

    # ✅ Fix Windows — ne crée le dossier que s'il n'existe pas déjà
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n  📊 RÉSUMÉ")
    print(f"  Total    : {len(results)}")
    print(f"  Succès   : {len(results) - errors}")
    print(f"  Erreurs  : {errors}")
    print(f"  Offres   : {sum(1 for r in results if r.get('job_offers'))}")
    print(f"  Contacts : {sum(1 for r in results if r.get('contact_form'))}")
    print(f"  💾 Sauvegardé → {output_file}")

    return EnrichSummary(
        total        = len(results),
        success      = len(results) - errors,
        errors       = errors,
        with_offers  = sum(1 for r in results if r.get("job_offers")),
        with_contact = sum(1 for r in results if r.get("contact_form")),
        output_file  = output_file,
    )


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrichit les entreprises du JSON via scraping.")
    parser.add_argument("--input",    default=None,      help="Chemin vers le JSON d'entrée")
    parser.add_argument("--output",   default=None,      help="Fichier JSON de sortie")
    parser.add_argument("--base-dir", default="results", help="Dossier de base")
    parser.add_argument("--limit",    type=int,          help="Nombre max d'entreprises")
    args = parser.parse_args()

    input_file  = args.input  or find_deep_results(args.base_dir)
    output_file = args.output or build_output_file(args.base_dir)

    run_enrich(input_file, output_file, args.limit)