import hashlib

from app.repositories.job_repository import JobRepository


def get_offers_from_pipeline(user_id: str) -> list[dict]:
    """Return job offers extracted from enriched companies in the local DB."""
    repo      = JobRepository()
    companies = [job.model_dump() for job in repo.find_by_stage(user_id, "enriched")]

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
