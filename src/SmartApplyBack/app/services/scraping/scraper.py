from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.scraping.scraping_config import MAX_WORKERS
from app.services.scraping.hunter_discover import discover_companies


def fetch_company_data(company: dict, sector: str, city: str) -> dict | None:
    domain = company.get("domain", "")
    name   = company.get("organization", domain)

    if not domain:
        return None

    return {
        "nom"    : name,
        "domaine": domain,
        "ville"  : city,
        "email"  : "",
        "secteur": sector,
    }


def scrape_companies(
    sector: str,
    cities: list,
    max_results: int = 100,
    keyword_match: str = "any",
) -> list:
    """
    Scrape companies via Hunter /discover.

    Args:
        sector:        search keywords
        cities:        target cities
        max_results:   max companies per city per sector
        keyword_match: Hunter keyword strategy — "any" or "all"
    """
    all_companies = []
    seen_domains  = set()

    for city in cities:
        raw_list = discover_companies(sector, city, max_results, keyword_match)
        unique   = _deduplicate(raw_list, seen_domains)
        results  = _fetch_all_parallel(unique, sector, city)

        for result in results:
            all_companies.append(result)
            seen_domains.add(result["domaine"])

    return all_companies


def _deduplicate(raw_list: list, global_seen: set) -> list:
    seen_in_batch = set()
    unique = []
    for company in raw_list:
        domain = company.get("domain", "")
        if domain and domain not in global_seen and domain not in seen_in_batch:
            seen_in_batch.add(domain)
            unique.append(company)
    return unique


def _fetch_all_parallel(companies: list, sector: str, city: str) -> list:
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