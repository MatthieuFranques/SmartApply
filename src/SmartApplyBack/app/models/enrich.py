# app/models/enrich.py

from pydantic import BaseModel
from typing import Optional


class EnrichRequest(BaseModel):
    input_file: str                    # ex: "results/toulouse/prospects.json"
    output_file: Optional[str] = None  # auto-généré si absent
    limit: Optional[int] = None        # nombre max d'entreprises


class EnrichSummary(BaseModel):
    total: int
    success: int
    errors: int
    with_offers: int
    with_contact: int
    output_file: str


class EnrichResponse(BaseModel):
    message: str
    summary: Optional[EnrichSummary] = None