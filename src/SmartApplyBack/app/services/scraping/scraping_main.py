# app/services/scraping/scraping_main.py

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scraper import scrape_companies
from json_utils import save_to_json, load_from_json

SECTORS = [
    "informatique", "développement logiciel", "agence web",
    "startup tech", "cybersécurité", "intelligence artificielle",
    "cloud computing", "édition logiciel", "conseil digital",
    "transformation digitale", "fintech", "ESN", "SSII",
    "software development", "web agency", "tech startup",
    "digital consulting", "digital transformation",
    "IT services", "IT consulting", "technology",
]

def run_scraping(cities: list = ["Toulouse", "Brussels", "Namur"], output_dir: str = "results"):
    """
    Lance le scraping pour toutes les villes et sauvegarde en UN seul fichier JSON.
    """
    os.makedirs(output_dir, exist_ok=True)

    # ─── Fichier unique pour toutes les villes ────────────────
    json_file = os.path.join(output_dir, "scraping_results.json")

    # Charge l'existant
    existing = load_from_json(json_file)
    if not existing:
        print(" Aucun fichier existant — démarrage from scratch")

    existing_domains = {c["domaine"] for c in existing}
    all_companies    = list(existing)

    summary = {}

    for city in cities:
        print(f"\n{'═'*50}")
        print(f" Ville : {city}")
        print(f"{'═'*50}")

        city_new = []

        for sector in SECTORS:
            print(f"\n Secteur : {sector}")
            results = scrape_companies(sector, [city])

            new = [r for r in results if r["domaine"] not in existing_domains]
            for r in new:
                existing_domains.add(r["domaine"])
                all_companies.append(r)
                city_new.append(r)

            print(f"   → {len(new)} nouveaux ajoutés")

        summary[city] = city_new
        print(f"\n   {len(city_new)} nouvelles entreprises pour {city}")

    # Déduplication & sauvegarde unique
    seen, unique = set(), []
    for c in all_companies:
        if c["domaine"] not in seen:
            seen.add(c["domaine"])
            unique.append(c)

    save_to_json(unique, json_file)

    # ─── Résumé global ────────────────────────────────────────
    print(f"\n{'═'*50}")
    print(f" Résumé final :")
    total = 0
    for city, companies in summary.items():
        n = len(companies)
        total += n
        print(f"  {city:<12} : {n} nouvelles entreprises")
    print(f"  {'TOTAL':<12} : {len(unique)} entreprises au total → {json_file}")

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scraping Hunter.io")
    parser.add_argument("--output-dir", default=".", help="Dossier de sortie")
    parser.add_argument("--cities", nargs="+", default=["Toulouse", "Brussels", "Namur"])
    args = parser.parse_args()

    run_scraping(cities=args.cities, output_dir=args.output_dir)