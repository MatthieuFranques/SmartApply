"""Tests for the SSE stream orchestrators (scraping / filter / enrich)."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.scraping import scraping_main
from app.services.enrich import enrich_main
from app.services.filters import filters_main
from app.services.enrich.enrich_config import CompanyContext


# ── stream_scraping ───────────────────────────────────────────

def test_stream_scraping_dedupes_and_saves():
    repo = MagicMock()
    companies = [
        {"domaine": "a.io", "nom": "A"},
        {"domaine": "a.io", "nom": "A dup"},  # dropped
        {"domaine": "b.io", "nom": "B"},
    ]
    with patch.object(scraping_main, "scrape_companies", return_value=companies):
        events = list(scraping_main.stream_scraping(["Lyon"], "u1", repo, sectors=["IT"]))

    types = [e["type"] for e in events]
    assert types[0] == "phase"
    assert types[-1] == "done"
    company_events = [e for e in events if e["type"] == "company"]
    assert len(company_events) == 2          # a.io + b.io
    assert events[-1]["total"] == 2
    assert repo.save_many.call_count == 2


# ── stream_enrich ─────────────────────────────────────────────

def test_stream_enrich_ok_and_error():
    repo = MagicMock()
    jobs = [
        {"domaine": "a.io", "nom": "A", "user_id": "u1"},
        {"domaine": "b.io", "nom": "B", "user_id": "u1"},
    ]

    ok_ctx = CompanyContext(nom="A", domaine="a.io", ville="", secteur="")
    ok_ctx.scrape_status = "ok"
    err_ctx = CompanyContext(nom="B", domaine="b.io", ville="", secteur="")
    err_ctx.scrape_status = "error"
    err_ctx.scrape_error = "boom"

    with patch.object(enrich_main, "enrich_company", side_effect=[ok_ctx, err_ctx]), \
         patch.object(enrich_main, "summarize_context", return_value="summary"), \
         patch.object(enrich_main.time, "sleep"):
        events = list(enrich_main.stream_enrich(jobs, "u1", repo))

    results = [e for e in events if e["type"] == "result"]
    assert {r["status"] for r in results} == {"ok", "error"}
    assert events[-1] == {"type": "done", "total": 2, "success": 1, "errors": 1}
    assert repo.update_stage.call_count == 2


def test_stream_enrich_respects_limit():
    repo = MagicMock()
    jobs = [{"domaine": f"{i}.io", "nom": str(i), "user_id": "u1"} for i in range(5)]
    ctx = CompanyContext(nom="x", domaine="x", ville="", secteur="")
    ctx.scrape_status = "ok"
    with patch.object(enrich_main, "enrich_company", return_value=ctx), \
         patch.object(enrich_main, "summarize_context", return_value="s"), \
         patch.object(enrich_main.time, "sleep"):
        events = list(enrich_main.stream_enrich(jobs, "u1", repo, limit=2))
    assert events[0] == {"type": "start", "total": 2}


# ── stream_pipeline ───────────────────────────────────────────

def test_stream_pipeline_skip_deep():
    repo = MagicMock()
    jobs = [{"domaine": "a.io", "nom": "A", "ville": "Lyon"}]
    kept = [{"domaine": "a.io", "nom": "A", "prescore": 7}]
    elim = [{"domaine": "z.io", "nom": "Z", "raison_filtre": "blacklist"}]

    with patch.object(filters_main, "prefilter_companies", return_value=(kept, elim)):
        events = list(filters_main.stream_pipeline(jobs, "u1", repo, skip_deep=True))

    statuses = {(e.get("step"), e.get("status")) for e in events if e["type"] == "result"}
    assert ("prefilter", "kept") in statuses
    assert ("prefilter", "eliminated") in statuses
    assert events[-1]["type"] == "done"
    assert events[-1]["total_pre_kept"] == 1


def test_stream_pipeline_with_deep_filter():
    repo = MagicMock()
    jobs = [{"domaine": "a.io", "nom": "A", "ville": "Lyon"}]
    kept = [{"domaine": "a.io", "nom": "A", "prescore": 7}]
    deep_kept = [{"domaine": "a.io", "nom": "A", "deep_score": 8}]

    with patch.object(filters_main, "prefilter_companies", return_value=(kept, [])), \
         patch.object(filters_main, "deep_filter_async",
                      new=AsyncMock(return_value=(deep_kept, []))):
        events = list(filters_main.stream_pipeline(jobs, "u1", repo))

    deep_results = [e for e in events if e.get("step") == "deep_filter" and e["type"] == "result"]
    assert deep_results and deep_results[0]["status"] == "kept"
    assert events[-1]["total_deep_kept"] == 1
