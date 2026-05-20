"""
indeed_rss.py → JSearch (RapidAPI)
-----------------------------------
Drop-in replacement for the former Indeed RSS scraper.
Requires JSEARCH_API_KEY env var (RapidAPI key).
Free tier: 200 requests/month.
"""

import hashlib
import os

import requests
from dotenv import load_dotenv

load_dotenv()

_API_KEY  = os.getenv("JSEARCH_API_KEY", "")
_BASE_URL = "https://jsearch.p.rapidapi.com/search"
_HEADERS  = {
    "X-RapidAPI-Key":  _API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}


def _days_to_param(days: int) -> str:
    if days <= 1:  return "today"
    if days <= 3:  return "3days"
    if days <= 7:  return "week"
    return "month"


def _map_job(job: dict) -> dict | None:
    url = job.get("job_apply_link") or job.get("job_google_link", "")
    if not url:
        return None

    city    = job.get("job_city", "") or ""
    country = job.get("job_country", "") or ""
    location = f"{city}, {country}".strip(", ")

    return {
        "id":              hashlib.md5(url.encode()).hexdigest(),
        "title":           job.get("job_title", ""),
        "company":         job.get("employer_name", ""),
        "location":        location,
        "url":             url,
        "description":     (job.get("job_description") or "")[:500],
        "date_posted":     (job.get("job_posted_at_datetime_utc") or "")[:10],
        "source":          "indeed",
        "status":          "new",
        "relevance_score": None,
        "tech_required":   [],
    }


def search_indeed(
    keywords:    str,
    location:    str = "France",
    days:        int = 30,
    max_results: int = 50,
) -> list[dict]:
    """
    Search jobs via JSearch (RapidAPI wrapper around Indeed + others).

    Args:
        keywords:    search query  (e.g. "développeur .NET fullstack")
        location:    city or country
        days:        only posts from the last N days
        max_results: cap results
    """
    if not _API_KEY:
        print("[JSearch] JSEARCH_API_KEY missing — skipping Indeed search")
        return []

    num_pages = min((max_results // 10) + 1, 3)

    params = {
        "query":       f"{keywords} in {location}",
        "page":        "1",
        "num_pages":   str(num_pages),
        "date_posted": _days_to_param(days),
        "language":    "fr",
    }

    try:
        resp = requests.get(_BASE_URL, params=params, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"[JSearch] {e}")
        return []

    results = [r for job in data if (r := _map_job(job))]
    return results[:max_results]
