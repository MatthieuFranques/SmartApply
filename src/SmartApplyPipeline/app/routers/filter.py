from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.services.filters.filters_main import stream_pipeline
from app.services.filters.filter_config import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user, AuthUser
from app.utils.sse import sse_event, SSE_HEADERS

router = APIRouter(prefix="/filter", tags=["Filter"])


@router.get("/stream")
def filter_stream(
    min_prescore:   int  = Query(default=MIN_PRESCORE),
    min_deep_score: int  = Query(default=MIN_DEEP_SCORE),
    concurrency:    int  = Query(default=CONCURRENCY),
    skip_deep:      bool = Query(default=False),
    current_user: AuthUser = Depends(get_current_user),
):
    repo = JobRepository()
    jobs = [j.model_dump() for j in repo.find_by_stage(current_user.google_id, "scraping")]

    def generate():
        if not jobs:
            yield sse_event({"type": "error", "message": "Aucun job à filtrer"})
            return
        for event in stream_pipeline(
            jobs, current_user.google_id, repo,
            min_prescore, min_deep_score, concurrency, skip_deep,
        ):
            yield sse_event(event)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/results")
def get_filtered_results(current_user: AuthUser = Depends(get_current_user)):
    repo = JobRepository()
    return [job.model_dump() for job in repo.find_by_stage(current_user.google_id, "deep")]