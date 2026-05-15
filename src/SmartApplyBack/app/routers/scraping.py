from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.services.scraping.scraping_main import stream_scraping
from app.services.scraping.scraping_config import DEFAULT_SECTORS
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.utils.sse import sse_event, SSE_HEADERS

router = APIRouter(prefix="/scraping", tags=["Scraping"])


@router.get("/stream")
def scrape_stream(
    cities:        str = Query(default="Toulouse"),
    sectors:       str = Query(default=""),
    max_results:   int = Query(default=100, ge=10, le=500),
    keyword_match: str = Query(default="any", pattern="^(any|all)$"),
    current_user: User = Depends(get_current_user),
):
    cities_list  = [c.strip() for c in cities.split(",") if c.strip()]
    sectors_list = [s.strip() for s in sectors.split(",") if s.strip()] or DEFAULT_SECTORS
    repo         = JobRepository()

    def generate():
        for event in stream_scraping(
            cities_list, current_user.google_id, repo,
            sectors_list, max_results, keyword_match,
        ):
            yield sse_event(event)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/config")
def get_scraping_config():
    """Returns default sectors and supported cities for the frontend UI."""
    from app.services.scraping.scraping_config import CITY_COUNTRY_MAP
    return {
        "default_sectors": DEFAULT_SECTORS,
        "supported_cities": sorted(CITY_COUNTRY_MAP.keys()),
    }