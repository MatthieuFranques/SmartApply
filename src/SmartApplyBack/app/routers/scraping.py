import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.services.scraping.scraping_main import stream_scraping
from app.models.scraping import ScrapingRequest
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.utils.sse import sse_event, SSE_HEADERS

router = APIRouter(prefix="/scraping", tags=["Scraping"])


@router.get("/stream")
def scrape_stream(
    cities: str = "Toulouse",
    current_user: User = Depends(get_current_user),
):
    cities_list = [c.strip() for c in cities.split(",")]
    repo = JobRepository()

    def generate():
        for event in stream_scraping(cities_list, current_user.google_id, repo):
            yield sse_event(event)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)