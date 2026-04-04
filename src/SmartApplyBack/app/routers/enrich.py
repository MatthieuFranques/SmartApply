# app/routers/enrich.py
import json
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.services.enrich.enrich_main import stream_enrich
from app.repositories.job_repository import JobRepository
from app.services.auth.dependency import get_current_user
from app.models.user import User

router = APIRouter(prefix="/enrich", tags=["Enrich"])


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/stream")
def enrich_stream(
    limit: int = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    repo = JobRepository()
    jobs = [j.model_dump() for j in repo.find_by_stage(current_user.google_id, "deep")]

    def generate():
        if not jobs:
            yield _sse({"type": "error", "message": "Aucun job à enrichir"})
            return
        for event in stream_enrich(jobs, current_user.google_id, repo, limit):
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