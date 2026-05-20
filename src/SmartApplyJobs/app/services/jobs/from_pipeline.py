"""
from_pipeline.py
----------------
Fetches enriched job offers from the pipeline service API.
Calls GET /enrich/results instead of reading MongoDB directly
to respect service boundaries.
"""

import hashlib
import os

import httpx

PIPELINE_URL     = os.getenv("PIPELINE_URL", "http://pipeline:8002")
PIPELINE_TIMEOUT = float(os.getenv("PIPELINE_TIMEOUT", "10"))


def get_offers_from_pipeline(user_id: str, access_token: str = "") -> list[dict]:
    """
    Returns job offers from enriched companies via the pipeline service API.
    Falls back to empty list if pipeline is unreachable.
    """
    try:
        resp = httpx.get(
            f"{PIPELINE_URL}/enrich/results",
            headers={"Cookie": f"session={access_token}"} if access_token else {},
            timeout=PIPELINE_TIMEOUT,
        )
        resp.raise_for_status()
        companies = resp.json()
    except Exception as e:
        print(f"[from_pipeline] pipeline unreachable: {e}", flush=True)
        return []

    results = []
    for company in companies:
        for offer in (company.get("job_offers") or []):
            url = offer.get("url", "")
            if not url or not offer.get("title"):
                continue
            results.append({
                "id":              hashlib.md5(url.encode()).hexdigest(),
                "title":           offer.get("title", ""),
                "company":         company.get("nom", ""),
                "location":        company.get("ville", ""),
                "url":             url,
                "description":     offer.get("description", "")[:500],
                "date_posted":     "",
                "source":          "pipeline",
                "status":          "new",
                "relevance_score": offer.get("relevance_score"),
                "tech_required":   offer.get("tech_required", []),
                "domaine":         company.get("domaine", ""),
                "secteur":         company.get("secteur", ""),
            })

    results.sort(key=lambda x: x.get("relevance_score") or 0, reverse=True)
    return results
