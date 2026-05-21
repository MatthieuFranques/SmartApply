from fastapi import APIRouter, HTTPException

from app.models.schemas import RetrieveContextRequest, RetrieveContextResponse
from app.services.retriever import get_letter_context

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


@router.post("/context", response_model=RetrieveContextResponse)
def retrieve_context(body: RetrieveContextRequest):
    try:
        context = get_letter_context(
            company=body.company,
            k_letters=body.k_letters,
            k_cv=body.k_cv,
            k_refs=body.k_refs,
        )
        return RetrieveContextResponse(**context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
