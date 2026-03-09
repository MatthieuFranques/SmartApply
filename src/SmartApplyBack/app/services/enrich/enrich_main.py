"""
enrich_main.py
--------------
Point d'entrée — enrichit les entreprises du JSON via scraping.

Usage:
    python enrich_main.py --input results/be/prospects.json --output results/be/enriched.json
    python enrich_main.py --input results/be/prospects.json --output results/be/enriched.json --limit 5
"""

import json
import time
import argparse
from dataclasses import asdict

from tqdm import tqdm

from enrich_pipeline import enrich_company, summarize_context


def load_json(filepath: str) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: list, filepath: str):
    import os
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Résultats sauvegardés dans {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Enrichit les entreprises du JSON via scraping.")
    parser.add_argument("--input",  required=True,           help="Chemin vers le JSON d'entrée")
    parser.add_argument("--output", default="enriched.json", help="Fichier JSON de sortie")
    parser.add_argument("--limit",  type=int, default=None,  help="Nombre max d'entreprises")
    args = parser.parse_args()

    rows = load_json(args.input)
    if args.limit:
        rows = rows[:args.limit]

    print(f"📋 {len(rows)} entreprise(s) à traiter\n")

    results, errors = [], 0

    for row in tqdm(rows, desc="Scraping", unit="entreprise"):
        ctx = enrich_company(row)
        results.append(asdict(ctx))

        if ctx.scrape_status != "ok":
            errors += 1
            tqdm.write(f"  ⚠️  {ctx.nom} — {ctx.scrape_status}: {ctx.scrape_error}")
        else:
            tqdm.write(f"  ✓  {summarize_context(ctx)}")

        time.sleep(1.5)

    save_json(results, args.output)

    with_offers  = sum(1 for r in results if r.get("job_offers"))
    with_contact = sum(1 for r in results if r.get("contact_form"))
    print(f"   {len(results) - errors} succès · {errors} erreurs")
    print(f"   {with_offers} avec offres · {with_contact} avec formulaire contact")


if __name__ == "__main__":
    main()