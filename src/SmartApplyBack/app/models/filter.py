from pydantic import BaseModel
from typing import List, Optional

class FilterRequest(BaseModel):
    cities: Optional[List[str]] = ["Toulouse", "Brussels", "Namur"]  # une ou plusieurs villes
    base_dir: Optional[str] = "results"
    min_prescore: Optional[int] = 4
    min_deep_score: Optional[int] = 6
    concurrency: Optional[int] = 10
    skip_deep: Optional[bool] = False

class FilterSummary(BaseModel):
    cities: List[str]
    output_dir: str
    pre_kept: int
    deep_kept: int
    paths: dict

class FilterResponse(BaseModel):
    message: str
    summary: Optional[FilterSummary] = None