import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import requests
from scraping_config import HUNTER_API_KEY, CITY_COUNTRY_MAP


def discover_companies(sector: str, city: str, max_results: int = 100, country: str = "FR") -> list:
    """
    Recherche des entreprises via /discover avec pagination.
    Contourne la limite de 100 par appel en faisant plusieurs pages.
    Chaque appel est GRATUIT.

    Paramètres :
        sector      : secteur ciblé
        city        : ville ciblée
        max_results : nombre max d'entreprises à récupérer (défaut 100)
        country     : code pays par défaut si la ville n'est pas dans CITY_COUNTRY_MAP

    Retourne :
        Liste de dicts bruts Hunter.
    """
    url     = "https://api.hunter.io/v2/discover"
    country = CITY_COUNTRY_MAP.get(city, country)
    all_results = []
    offset      = 0
    limit       = 100  # max par appel selon la doc Hunter

    while len(all_results) < max_results:
        payload = {
            "headquarters_location": {
                "include": [{"city": city, "country": country}]
            },
            "keywords": {
                "include": sector.split(),
                "match"  : "any"
            },
            "limit" : limit,
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
                break  # plus de résultats disponibles

            all_results.extend(results)
            offset += len(results)

            if len(results) < limit:
                break  # dernière page atteinte

        except Exception as e:
            print(f"  [Discover] Erreur page offset={offset} : {e}")
            break

    return all_results[:max_results]