# app/models/enrich.py

from pydantic import BaseModel
from typing import Optional

class EnrichRequest(BaseModel):
    input_file:  Optional[str] = None   # ← optionnel maintenant
    output_file: Optional[str] = None
    base_dir:    Optional[str] = "results"
    limit:       Optional[int] = None

class EnrichSummary(BaseModel):
    total:        int
    success:      int
    errors:       int
    with_offers:  int
    with_contact: int
    output_file:  str

class EnrichResponse(BaseModel):
    message: str
    summary: Optional[EnrichSummary] = None