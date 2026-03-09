from pydantic import BaseModel
from typing import List, Optional

class FilterRequest(BaseModel):
    input_file: str                                   
    output_dir: Optional[str] = None                  
    min_prescore: Optional[int] = 4
    min_deep_score: Optional[int] = 6
    concurrency: Optional[int] = 10
    skip_deep: Optional[bool] = False

class FilterSummary(BaseModel):
    input_file: str
    output_dir: str
    pre_kept: int
    deep_kept: int
    paths: dict

class FilterResponse(BaseModel):
    message: str
    summary: Optional[FilterSummary] = None