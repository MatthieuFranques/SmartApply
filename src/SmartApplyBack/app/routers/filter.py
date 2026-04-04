# app/routers/filter.py
import json
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.services.filters.filters_main import stream_pipeline
from app.services.filters.filter_config import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User

router = APIRouter(prefix="/filter", tags=["Filter"])


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/stream")
def filter_stream(
    min_prescore:   int  = Query(default=MIN_PRESCORE),
    min_deep_score: int  = Query(default=MIN_DEEP_SCORE),
    concurrency:    int  = Query(default=CONCURRENCY),
    skip_deep:      bool = Query(default=False),
    current_user: User = Depends(get_current_user),
):
    repo = JobRepository()
    jobs = [j.model_dump() for j in repo.find_by_stage(current_user.google_id, "scraping")]

    def generate():
        if not jobs:
            yield _sse({"type": "error", "message": "Aucun job à filtrer"})
            return
        for event in stream_pipeline(
            jobs, current_user.google_id, repo,
            min_prescore, min_deep_score, concurrency, skip_deep
        ):
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