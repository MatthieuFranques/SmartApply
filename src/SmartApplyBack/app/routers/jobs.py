from fastapi import APIRouter, Depends, Query

from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.services.jobs.from_pipeline import get_offers_from_pipeline
from app.services.jobs.indeed_rss import search_indeed

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/offers")
def get_offers(
    source:   str = Query(default="all", pattern="^(all|pipeline|indeed)$"),
    keywords: str = Query(default=""),
    location: str = Query(default=""),
    days:     int = Query(default=30, ge=1, le=90),
    limit:    int = Query(default=100, ge=1, le=300),
    current_user: User = Depends(get_current_user),
):
    """
    Returns job offers from multiple sources.

    Sources:
    - pipeline: offers found during enrichment phase (from MongoDB)
    - indeed:   fresh offers from Indeed RSS (requires keywords)
    - all:      both combined (default)
    """
    results: list[dict] = []

    if source in ("all", "pipeline"):
        results += get_offers_from_pipeline(current_user.google_id)

    if source in ("all", "indeed") and keywords.strip():
        loc = location.strip() or "France"
        results += search_indeed(keywords.strip(), loc, days, limit)

    # Dedup by id (pipeline + indeed may overlap for same URL)
    seen: set[str] = set()
    unique = []
    for offer in results:
        if offer["id"] not in seen:
            seen.add(offer["id"])
            unique.append(offer)

    return unique[:limit]
