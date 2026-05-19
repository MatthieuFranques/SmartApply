from pydantic import BaseModel


class IndexLetterRequest(BaseModel):
    letter_text: str
    company: dict
    mode: str
    user_id: str = "default"


class IndexCVRequest(BaseModel):
    profile: dict
    user_id: str = "default"


class IndexCompanyRequest(BaseModel):
    company: dict


class IndexReferenceRequest(BaseModel):
    letter_text: str
    source: str
    company_type: str = "generic"


class IndexResponse(BaseModel):
    success: bool
    doc_ids: list[str]
    collection: str


class RetrieveContextRequest(BaseModel):
    company: dict
    k_letters: int = 3
    k_cv: int = 3
    k_refs: int = 2


class RetrieveContextResponse(BaseModel):
    similar_letters: list[str] = []
    cv_chunks: list[str] = []
    reference_letters: list[str] = []
    has_context: bool = False
