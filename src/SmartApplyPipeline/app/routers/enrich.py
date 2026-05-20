from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.services.enrich.enrich_main import stream_enrich
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User
from app.utils.sse import sse_event, SSE_HEADERS

router = APIRouter(prefix="/enrich", tags=["Enrich"])


@router.get("/stream")
def enrich_stream(
    limit: int = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    repo = JobRepository()
    jobs = [j.model_dump() for j in repo.find_by_stage(current_user.google_id, "deep")]

    def generate():
        if not jobs:
            yield sse_event({"type": "done", "total": 0, "success": 0, "errors": 0})
            return
        for event in stream_enrich(jobs, current_user.google_id, repo, limit):
            yield sse_event(event)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/results")
def get_enriched_results(current_user: User = Depends(get_current_user)):
    repo = JobRepository()
    return [job.model_dump() for job in repo.find_by_stage(current_user.google_id, "enriched")]