from app.services.scraping.scraper import scrape_companies
from app.services.scraping.scraping_config import DEFAULT_SECTORS


def stream_scraping(
    cities: list[str],
    user_id: str,
    repo,
    sectors: list[str] | None = None,
    max_results: int = 100,
    keyword_match: str = "any",
):
    if not sectors:
        sectors = DEFAULT_SECTORS

    seen_domains: set[str] = set()
    total_found = 0

    yield {"type": "phase", "status": "started", "phase": "scraping"}

    for city in cities:
        yield {"type": "info", "message": f"Recherche en cours à {city}..."}

        for sector in sectors:
            results = scrape_companies(sector, [city], max_results, keyword_match)

            for company in results:
                domaine = company.get("domaine")

                if domaine and domaine not in seen_domains:
                    seen_domains.add(domaine)
                    total_found += 1

                    repo.save_many([company], user_id, stage="scraping")

                    yield {
                        "type"   : "company",
                        "phase"  : "scraping",
                        "company": company.get("nom", domaine),
                        "domaine": domaine,
                        "city"   : city,
                    }

    yield {"type": "done", "phase": "scraping", "total": total_found}