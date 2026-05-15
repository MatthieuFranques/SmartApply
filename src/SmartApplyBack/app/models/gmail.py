from pydantic import BaseModel
from typing import Optional


class GmailMessage(BaseModel):
    id:          str
    subject:     Optional[str] = None
    sender:      Optional[str] = None
    received_at: Optional[str] = None
    body:        Optional[str] = None
    links:       list[str]     = []
    label:       Optional[str] = None


class DraftRequest(BaseModel):
    domaine: str
    model:   str = "mistral"


class DraftResponse(BaseModel):
    draft_id:  str
    draft_url: str
    to:        str
    subject:   str