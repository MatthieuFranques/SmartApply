from fastapi import APIRouter, Depends, Query

from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.services.jobs.from_pipeline import get_offers_from_pipeline
from app.services.jobs.indeed_rss import search_indeed
from app.services.jobs.adzuna import search_adzuna
from app.services.jobs.search_cache import get_cached, set_cached
from app.repositories.job_offer_repository import (
    upsert_offers, find_offers, find_offers_grouped, count_offers,
)

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
    results: list[dict] = []

    if source in ("all", "pipeline"):
        results += get_offers_from_pipeline(current_user.google_id)

    if source in ("all", "indeed"):
        kw  = keywords.strip()
        loc = location.strip() or "France"

        if kw:
            cached = get_cached(kw, loc, days)
            if cached is not None:
                results += cached
            else:
                external = []
                external += search_indeed(kw, loc, days, limit)
                external += search_adzuna(kw, loc, days, limit)

                if external:
                    set_cached(kw, loc, days, external)
                    upsert_offers(current_user.google_id, external, kw, loc)

                results += external
        else:
            results += find_offers(current_user.google_id)

    seen: set[str] = set()
    unique = []
    for offer in results:
        if offer["id"] not in seen:
            seen.add(offer["id"])
            unique.append(offer)

    return unique[:limit]


@router.get("/stored/grouped")
def get_stored_grouped(current_user: User = Depends(get_current_user)):
    return find_offers_grouped(current_user.google_id)


@router.get("/stored/count")
def get_stored_count(current_user: User = Depends(get_current_user)):
    return {"count": count_offers(current_user.google_id)}
