"""Smoke tests for Pydantic request/response models (construction + defaults)."""

from app.models.enrich import EnrichRequest, EnrichSummary, EnrichResponse
from app.models.filter import FilterRequest, FilterSummary, FilterResponse
from app.models.letter import (
    CompanySearchRequest, GenerateRequest, GenerateResponse, LetterItem,
)
from app.models.scraping import ScrapingRequest, ScrapingResponse


def test_enrich_models():
    assert EnrichRequest().limit is None
    summary = EnrichSummary(total=2, success=1, errors=1, with_offers=1, with_contact=0)
    assert EnrichResponse(message="ok", summary=summary).summary.total == 2


def test_filter_models():
    assert FilterRequest().min_prescore == 4
    summary = FilterSummary(cities=["Lyon"], output_dir="x", pre_kept=3, deep_kept=1, paths={})
    assert FilterResponse(message="done", summary=summary).summary.deep_kept == 1


def test_letter_models():
    assert GenerateRequest(name="Acme").model == "mistral"
    assert CompanySearchRequest(name="Acme").name == "Acme"
    resp = GenerateResponse(company="Acme", filename="f", mode="letter", model="m", output_dir="d")
    assert resp.company == "Acme"
    assert LetterItem(filename="f", size_kb=1.2, path="p").size_kb == 1.2


def test_scraping_models():
    assert ScrapingRequest().cities == ["Toulouse", "Brussels", "Namur"]
    assert ScrapingResponse(message="ok", cities=["Lyon"]).cities == ["Lyon"]
