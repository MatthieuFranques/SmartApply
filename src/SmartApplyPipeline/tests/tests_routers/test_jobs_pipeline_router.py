"""Router tests for /jobs and /pipeline/config."""

from unittest.mock import patch

from app.routers import jobs as jobs_router


# ── /pipeline/config ──────────────────────────────────────────

def test_pipeline_config_no_auth(client):
    resp = client.get("/pipeline/config")
    assert resp.status_code == 200
    body = resp.json()
    assert "scraping" in body and "filter" in body


# ── /jobs/offers ──────────────────────────────────────────────

def test_offers_pipeline_source(auth_client):
    offers = [{"id": "a1", "title": "Dev"}]
    with patch.object(jobs_router, "get_offers_from_pipeline", return_value=offers):
        resp = auth_client.get("/jobs/offers", params={"source": "pipeline"})
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Dev"


def test_offers_indeed_cache_hit(auth_client):
    cached = [{"id": "b1", "title": "Cached Dev"}]
    with patch.object(jobs_router, "get_cached", return_value=cached), \
         patch.object(jobs_router, "search_indeed") as mock_indeed:
        resp = auth_client.get("/jobs/offers", params={"source": "indeed", "keywords": "python"})
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "b1"
    mock_indeed.assert_not_called()  # cache short-circuits external search


def test_offers_indeed_cache_miss_searches_and_stores(auth_client):
    with patch.object(jobs_router, "get_cached", return_value=None), \
         patch.object(jobs_router, "search_indeed", return_value=[{"id": "c1", "title": "Fresh"}]), \
         patch.object(jobs_router, "search_adzuna", return_value=[]), \
         patch.object(jobs_router, "set_cached") as mock_set, \
         patch.object(jobs_router, "upsert_offers") as mock_upsert:
        resp = auth_client.get("/jobs/offers", params={"source": "indeed", "keywords": "python"})
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "c1"
    mock_set.assert_called_once()
    mock_upsert.assert_called_once()


def test_offers_dedupes_by_id(auth_client):
    dupes = [{"id": "x", "title": "A"}, {"id": "x", "title": "B"}]
    with patch.object(jobs_router, "get_offers_from_pipeline", return_value=dupes):
        resp = auth_client.get("/jobs/offers", params={"source": "pipeline"})
    assert len(resp.json()) == 1


def test_stored_count(auth_client):
    with patch.object(jobs_router, "count_offers", return_value=7):
        resp = auth_client.get("/jobs/stored/count")
    assert resp.json() == {"count": 7}


def test_stored_grouped(auth_client):
    grouped = [{"keywords": "python", "location": "france", "offers": [], "count": 0}]
    with patch.object(jobs_router, "find_offers_grouped", return_value=grouped):
        resp = auth_client.get("/jobs/stored/grouped")
    assert resp.status_code == 200
    assert resp.json()[0]["keywords"] == "python"
