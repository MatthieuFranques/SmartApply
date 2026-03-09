# app/services/scraping_main.py

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scraper import scrape_companies
from json_utils import save_to_json, load_from_json

# ─── Configuration ───────────────────────────────────────────

SECTORS = [
    "informatique", "développement logiciel", "agence web",
    "startup tech", "cybersécurité", "intelligence artificielle",
    "cloud computing", "édition logiciel", "conseil digital",
    "transformation digitale", "fintech", "ESN", "SSII",
    "software development", "web agency", "tech startup",
    "digital consulting", "digital transformation",
    "IT services", "IT consulting", "technology",
]

# ─── Fonction principale ─────────────────────────────────────

def run_scraping(cities: list = ["Toulouse", "Brussels", "Namur"], output_dir: str = "results"):
    """
    Lance le scraping pour les villes données et sauvegarde les résultats en JSON.
    Appelable par le router FastAPI ou en ligne de commande.
    """
    os.makedirs(output_dir, exist_ok=True)
    summary = {}

    for city in cities:
        json_file = os.path.join(output_dir, f"scraping_results_{city.lower()}.json")
        print(f"\n{'═'*50}")
        print(f"🌍 Ville : {city}  →  {json_file}")
        print(f"{'═'*50}")

        # Charge l'existant pour cette ville
        existing = load_from_json(json_file)
        if not existing:
            print("📂 Aucun fichier existant — démarrage from scratch")

        existing_domains = {c["domaine"] for c in existing}
        all_companies    = list(existing)

        # Scrape chaque secteur pour cette ville
        for sector in SECTORS:
            print(f"\n🚀 Secteur : {sector}")
            results = scrape_companies(sector, [city])

            new = [r for r in results if r["domaine"] not in existing_domains]
            for r in new:
                existing_domains.add(r["domaine"])
                all_companies.append(r)

            print(f"   → {len(new)} nouveaux ajoutés")

        # Déduplication & sauvegarde
        seen, unique = set(), []
        for c in all_companies:
            if c["domaine"] not in seen:
                seen.add(c["domaine"])
                unique.append(c)

        save_to_json(unique, json_file)
        summary[city] = unique

    # ─── Résumé global ───────────────────────────────────────

    print(f"\n{'═'*50}")
    print(f"📊 Résumé final :")
    total = 0
    for city, companies in summary.items():
        n = len(companies)
        total += n
        print(f"  {city:<12} : {n} entreprises  →  entreprises_{city.lower()}.json")
    print(f"  {'TOTAL':<12} : {total} entreprises")

    return summary


# ─── CLI (optionnel) ─────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scraping Hunter.io")
    parser.add_argument("--output-dir", default=".", help="Dossier de sortie pour les JSON")
    parser.add_argument("--cities", nargs="+", default=["Toulouse", "Brussels", "Namur"],
                        help="Villes à scraper (ex: --cities Toulouse Brussels Namur)")
    args = parser.parse_args()

    run_scraping(cities=args.cities, output_dir=args.output_dir)