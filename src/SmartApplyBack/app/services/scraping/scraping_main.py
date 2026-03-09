import os
import sys
import argparse
"""
python scraping_main.py --cities Toulouse Namur --output-dir ../../results
python scraping_main.py --output-dir ../../results
    # → results/entreprises_toulouse.csv
    # → results/entreprises_brussels.csv
    # → results/entreprises_namur.csv
"""
sys.path.insert(0, os.path.dirname(__file__))

from scraper import scrape_companies
from csv_utils import save_to_csv, load_from_csv

# ─── Arguments CLI ───────────────────────────────────────────

parser = argparse.ArgumentParser(description="Scraping Hunter.io")
parser.add_argument("--output-dir", default=".",
                    help="Dossier de sortie pour les CSV (défaut : dossier courant)")
parser.add_argument("--cities", nargs="+", default=["Toulouse", "Brussels", "Namur"],
                    help="Villes à scraper (ex: --cities Toulouse Brussels Namur)")
args = parser.parse_args()

OUTPUT_DIR = args.output_dir
CITIES     = args.cities

os.makedirs(OUTPUT_DIR, exist_ok=True)

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

# ─── Scraping par ville ──────────────────────────────────────

summary = {}

for city in CITIES:
    csv_file = os.path.join(OUTPUT_DIR, f"entreprises_{city.lower()}.csv")
    print(f"\n{'═'*50}")
    print(f"🌍 Ville : {city}  →  {csv_file}")
    print(f"{'═'*50}")

    # Charge l'existant pour cette ville
    if os.path.exists(csv_file):
        existing = load_from_csv(csv_file)
    else:
        existing = []
        print("📂 Aucun fichier existant — démarrage from scratch")

    existing_domains = {c["domaine"] for c in existing}
    all_companies    = list(existing)

    # Scrape chaque secteur pour cette ville uniquement
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

    save_to_csv(unique, csv_file)
    summary[city] = unique

# ─── Résumé global ───────────────────────────────────────────

print(f"\n{'═'*50}")
print(f"📊 Résumé final :")
total = 0
for city, companies in summary.items():
    n = len(companies)
    total += n
    print(f"  {city:<12} : {n} entreprises  →  entreprises_{city.lower()}.csv")
print(f"  {'TOTAL':<12} : {total} entreprises")