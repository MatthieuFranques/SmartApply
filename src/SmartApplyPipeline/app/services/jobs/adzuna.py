import hashlib
import os

import requests
from dotenv import load_dotenv

load_dotenv()

_APP_ID   = os.getenv("ADZUNA_APP_ID", "")
_APP_KEY  = os.getenv("ADZUNA_APP_KEY", "")
_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

_COUNTRY_MAP = {
    "france": "fr", "fr": "fr",
    "belgique": "be", "belgium": "be", "be": "be",
    "suisse": "ch", "switzerland": "ch", "ch": "ch",
    "luxembourg": "lu", "lu": "lu",
    "uk": "gb", "royaume-uni": "gb", "london": "gb",
    "germany": "de", "allemagne": "de", "berlin": "de",
    "netherlands": "nl", "amsterdam": "nl",
    "spain": "es", "espagne": "es", "madrid": "es", "barcelona": "es",
}


def _resolve_country(location: str) -> str:
    key = location.lower().strip()
    for fragment, code in _COUNTRY_MAP.items():
        if fragment in key:
            return code
    return "fr"


def _map_job(job: dict, location: str) -> dict | None:
    url = job.get("redirect_url", "")
    if not url:
        return None

    loc_parts  = [job.get("location", {}).get("display_name", ""), location]
    display_loc = loc_parts[0] or loc_parts[1]
    created     = (job.get("created") or "")[:10]

    return {
        "id":              hashlib.md5(url.encode()).hexdigest(),
        "title":           job.get("title", ""),
        "company":         (job.get("company") or {}).get("display_name", ""),
        "location":        display_loc,
        "url":             url,
        "description":     (job.get("description") or "")[:500],
        "date_posted":     created,
        "source":          "indeed",
        "status":          "new",
        "relevance_score": None,
        "tech_required":   [],
    }


def search_adzuna(
    keywords:    str,
    location:    str = "France",
    days:        int = 30,
    max_results: int = 50,
) -> list[dict]:
    if not _APP_ID or not _APP_KEY:
        print("[Adzuna] ADZUNA_APP_ID or ADZUNA_APP_KEY missing — skipping")
        return []

    country  = _resolve_country(location)
    per_page = min(max_results, 50)
    url      = f"{_BASE_URL}/{country}/search/1"

    params = {
        "app_id":           _APP_ID,
        "app_key":          _APP_KEY,
        "what":             keywords,
        "where":            location,
        "max_days_old":     str(days),
        "results_per_page": str(per_page),
        "content-type":     "application/json",
        "sort_by":          "date",
    }

    try:
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except Exception as e:
        print(f"[Adzuna] {e}")
        return []

    results = [r for job in data if (r := _map_job(job, location))]
    return results[:max_results]
