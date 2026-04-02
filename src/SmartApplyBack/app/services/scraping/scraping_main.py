# app/services/scraping/scraping_main.py

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scraper import scrape_companies

SECTORS = [
    "informatique", "développement logiciel", "agence web",
    "startup tech", "cybersécurité", "intelligence artificielle",
    "cloud computing", "édition logiciel", "conseil digital",
    "transformation digitale", "fintech", "ESN", "SSII",
    "software development", "web agency", "tech startup",
    "digital consulting", "digital transformation",
    "IT services", "IT consulting", "technology",
]


def run_scraping(cities: list[str] = ["Toulouse", "Brussels", "Namur"]) -> list[dict]:
    """
    Lance le scraping pour toutes les villes.
    Retourne la liste complète des entreprises trouvées (dédupliquées).
    La déduplication inter-sessions est gérée par MongoDB (upsert sur domaine).
    """
    seen_domains: set[str] = set()
    all_companies: list[dict] = []

    for city in cities:
        print(f"\n{'═'*50}")
        print(f"  Ville : {city}")
        print(f"{'═'*50}")

        for sector in SECTORS:
            print(f"\n  Secteur : {sector}")
            results = scrape_companies(sector, [city])

            for company in results:
                if company["domaine"] not in seen_domains:
                    seen_domains.add(company["domaine"])
                    all_companies.append(company)
                    print(f"    → ajouté : {company['domaine']}")

    print(f"\n{'═'*50}")
    print(f"  TOTAL : {len(all_companies)} entreprises trouvées")
    print(f"{'═'*50}")

    return all_companies  # ← list[dict], la DB gère la déduplication via upsert


if __name__ == "__main__":
    import argparse
    from app.repositories.job_repository import JobRepository

    parser = argparse.ArgumentParser(description="Scraping Hunter.io")
    parser.add_argument("--cities", nargs="+", default=["Toulouse", "Brussels", "Namur"])
    parser.add_argument("--user-id", required=True, help="google_id de l'utilisateur")
    args = parser.parse_args()

    results = run_scraping(cities=args.cities)
    JobRepository().save_many(results, args.user_id, stage="scraping")
    print(f"  {len(results)} entreprises sauvegardées en DB")