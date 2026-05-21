from fastapi import APIRouter

from app.services.scraping.scraping_config import DEFAULT_SECTORS, CITY_COUNTRY_MAP
from app.services.filters.filter_config import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.get("/config")
def get_pipeline_config():
    """Returns all configurable parameters for the full pipeline with defaults and ranges."""
    return {
        "scraping": {
            "supported_cities": sorted(CITY_COUNTRY_MAP.keys()),
            "default_sectors":  DEFAULT_SECTORS,
            "max_results":      {"default": 100, "min": 10, "max": 300, "step": 10},
            "keyword_match":    {"default": "any", "options": ["any", "all"]},
        },
        "filter": {
            "min_prescore":   {"default": MIN_PRESCORE,   "min": 0, "max": 10},
            "min_deep_score": {"default": MIN_DEEP_SCORE, "min": 0, "max": 10},
            "skip_deep":      {"default": False},
        },
    }