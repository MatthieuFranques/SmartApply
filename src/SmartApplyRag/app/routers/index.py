from fastapi import APIRouter, HTTPException

from app.config import COLLECTIONS
from app.models.schemas import (
    IndexCVRequest,
    IndexCompanyRequest,
    IndexLetterRequest,
    IndexReferenceRequest,
    IndexResponse,
)
from app.services import indexer

router = APIRouter(prefix="/index", tags=["index"])


@router.post("/letter", response_model=IndexResponse, status_code=201)
def index_letter(body: IndexLetterRequest):
    try:
        doc_id = indexer.index_letter(body.letter_text, body.company, body.mode, body.user_id)
        return IndexResponse(success=True, doc_ids=[doc_id], collection=COLLECTIONS["letters"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cv", response_model=IndexResponse, status_code=201)
def index_cv(body: IndexCVRequest):
    try:
        ids = indexer.index_cv_profile(body.profile, body.user_id)
        return IndexResponse(success=True, doc_ids=ids, collection=COLLECTIONS["cv_chunks"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company", response_model=IndexResponse, status_code=201)
def index_company(body: IndexCompanyRequest):
    try:
        doc_id = indexer.index_company(body.company)
        return IndexResponse(success=True, doc_ids=[doc_id], collection=COLLECTIONS["companies"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reference", response_model=IndexResponse, status_code=201)
def index_reference(body: IndexReferenceRequest):
    try:
        doc_id = indexer.index_reference_letter(body.letter_text, body.source, body.company_type)
        return IndexResponse(success=True, doc_ids=[doc_id], collection=COLLECTIONS["references"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
