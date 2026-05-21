import requests
from app.services.scraping.scraping_config import HUNTER_API_KEY, get_country


def discover_companies(
    sector: str,
    city: str,
    max_results: int = 100,
    keyword_match: str = "any",
) -> list:
    """
    Fetch companies via Hunter /discover with pagination.
    Each call is free on Hunter.io.

    Args:
        sector:        search keywords (space-separated)
        city:          target city
        max_results:   max companies to retrieve
        keyword_match: "any" or "all" (Hunter keyword matching strategy)
    """
    url         = "https://api.hunter.io/v2/discover"
    country     = get_country(city)
    all_results = []
    offset      = 0
    limit       = 100  # Hunter max per call

    while len(all_results) < max_results:
        payload = {
            "headquarters_location": {
                "include": [{"city": city, "country": country}]
            },
            "keywords": {
                "include": sector.split(),
                "match":   keyword_match,
            },
            "limit":  min(limit, max_results - len(all_results)),
            "offset": offset,
        }

        try:
            response = requests.post(
                url,
                json    = payload,
                params  = {"api_key": HUNTER_API_KEY},
                headers = {"Content-Type": "application/json"},
                timeout = 10,
            )
            response.raise_for_status()
            results = response.json().get("data", [])

            if not results:
                break

            all_results.extend(results)
            offset += len(results)

            if len(results) < limit:
                break

        except Exception as e:
            print(f"  [Discover] Error at offset={offset}: {e}")
            break

    return all_results[:max_results]