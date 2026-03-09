# app/models/scraping.py

from pydantic import BaseModel
from typing import List, Optional

class ScrapingRequest(BaseModel):
    cities: Optional[List[str]] = ["Toulouse", "Brussels", "Namur"]
    output_dir: Optional[str] = "results"

class ScrapingResponse(BaseModel):
    message: str
    cities: List[str]
    output_dir: str