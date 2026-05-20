"""
from_pipeline.py
----------------
Aggregate job_offers already scraped during enrichment phase,
stored in MongoDB as part of each enriched company document.
"""

import hashlib
from app.repositories.job_repository import JobRepository


def get_offers_from_pipeline(user_id: str) -> list[dict]:
    """
    Returns all job offers from enriched companies for this user.
    Each offer is enriched with company metadata.
    """
    repo    = JobRepository()
    jobs    = repo.find_by_stage(user_id, "enriched")
    results = []

    for job in jobs:
        j = job.model_dump()
        for offer in (j.get("job_offers") or []):
            url = offer.get("url", "")
            if not url or not offer.get("title"):
                continue
            results.append({
                "id":              hashlib.md5(url.encode()).hexdigest(),
                "title":           offer.get("title", ""),
                "company":         j.get("nom", ""),
                "location":        j.get("ville", ""),
                "url":             url,
                "description":     offer.get("description", "")[:500],
                "date_posted":     "",
                "source":          "pipeline",
                "status":          "new",
                "relevance_score": offer.get("relevance_score"),
                "tech_required":   offer.get("tech_required", []),
                "domaine":         j.get("domaine", ""),
                "secteur":         j.get("secteur", ""),
            })

    results.sort(key=lambda x: x.get("relevance_score") or 0, reverse=True)
    return results
