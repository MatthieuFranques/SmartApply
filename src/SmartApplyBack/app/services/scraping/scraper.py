from concurrent.futures import ThreadPoolExecutor, as_completed

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from scraping_config import CITY_COUNTRY_MAP, MAX_WORKERS
from hunter_discover import discover_companies


def fetch_company_data(company: dict, sector: str, city: str) -> dict | None:
    """
    Traite une seule entreprise depuis les données brutes /discover.
    La recherche d'email (hunter_domain) est désactivée volontairement
    pour éviter les 429 — le fichier hunter_domain.py est conservé si besoin plus tard.

    Retourne :
        Dict structuré avec nom, domaine, ville, email (vide), secteur — ou None si domaine vide.
    """
    domain = company.get("domain", "")
    name   = company.get("organization", domain)

    if not domain:
        return None

    print(f"  ✅ {name}")

    return {
        "nom"    : name,
        "domaine": domain,
        "ville"  : city,
        "email"  : "",
        "secteur": sector,
    }


def scrape_companies(sector: str, cities: list) -> list:
    """
    Scraping via /discover uniquement (aucun appel /domain-search).

    Paramètres :
        sector : secteur ciblé, ex. "agence web"
        cities : liste de villes, ex. ["Toulouse", "Bruxelles"]

    Retourne :
        Liste de dicts avec : nom, domaine, ville, email, secteur.
    """
    all_companies = []
    seen_domains  = set()

    for city in cities:
        if city not in CITY_COUNTRY_MAP:
            print(f"  ⚠️  '{city}' absent du CITY_COUNTRY_MAP — ville ignorée")
            continue

        country = CITY_COUNTRY_MAP[city]
        print(f"\n🔍 Discover : '{sector}' à {city} ({country})...")

        raw_list = discover_companies(sector, city, max_results=100)
        print(f"   → {len(raw_list)} entreprises trouvées")

        unique = _deduplicate(raw_list, seen_domains)
        print(f"   → {len(unique)} uniques à traiter...")

        results = _fetch_all_parallel(unique, sector, city)

        for result in results:
            all_companies.append(result)
            seen_domains.add(result["domaine"])

    return all_companies


# ─── Helpers privés ──────────────────────────────────────────

def _deduplicate(raw_list: list, global_seen: set) -> list:
    """Filtre les doublons au sein d'un batch et par rapport aux batches précédents."""
    seen_in_batch = set()
    unique = []

    for company in raw_list:
        domain = company.get("domain", "")
        if domain and domain not in global_seen and domain not in seen_in_batch:
            seen_in_batch.add(domain)
            unique.append(company)

    return unique


def _fetch_all_parallel(companies: list, sector: str, city: str) -> list:
    """Traite les entreprises en parallèle via ThreadPoolExecutor."""
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_company_data, company, sector, city): company
            for company in companies
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    return results