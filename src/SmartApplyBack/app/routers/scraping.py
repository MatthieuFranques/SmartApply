# app/routers/scraping.py
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.services.scraping.scraping_main import stream_scraping
from app.models.scraping import ScrapingRequest
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User

router = APIRouter(prefix="/scraping", tags=["Scraping"])


def _sse(data: dict) -> str:
    """Formate un dict en événement SSE."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/stream")
def scrape_stream(
    cities: str = "Toulouse",
    current_user: User = Depends(get_current_user),
):
    """Stream SSE — envoie chaque entreprise trouvée en temps réel."""
    cities_list = [c.strip() for c in cities.split(",")]
    repo = JobRepository()

    def generate():
        for event in stream_scraping(cities_list, current_user.google_id, repo):
            yield _sse(event)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "http://localhost:4200",
        },
    )