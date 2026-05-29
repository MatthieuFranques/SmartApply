"""Router tests for /filter and /enrich (streams + results + company lookup)."""

from unittest.mock import MagicMock, patch

from app.routers import filter as filter_router
from app.routers import enrich as enrich_router


def _job(d: dict):
    m = MagicMock()
    m.model_dump.return_value = d
    return m


# ── /filter ───────────────────────────────────────────────────

def test_filter_stream_no_jobs_emits_error(auth_client):
    repo = MagicMock()
    repo.find_by_stage.return_value = []
    with patch.object(filter_router, "JobRepository", return_value=repo):
        resp = auth_client.get("/filter/stream")
    assert resp.status_code == 200
    assert "Aucun job" in resp.text


def test_filter_stream_runs_pipeline(auth_client):
    repo = MagicMock()
    repo.find_by_stage.return_value = [_job({"domaine": "acme.io"})]

    def fake_pipeline(*a, **k):
        yield {"type": "done"}

    with patch.object(filter_router, "JobRepository", return_value=repo), \
         patch.object(filter_router, "stream_pipeline", side_effect=fake_pipeline):
        resp = auth_client.get("/filter/stream")
    assert resp.status_code == 200
    assert '"type": "done"' in resp.text


def test_filter_results(auth_client):
    repo = MagicMock()
    repo.find_by_stage.return_value = [_job({"domaine": "acme.io", "stage": "deep"})]
    with patch.object(filter_router, "JobRepository", return_value=repo):
        resp = auth_client.get("/filter/results")
    assert resp.status_code == 200
    assert resp.json()[0]["domaine"] == "acme.io"


# ── /enrich ───────────────────────────────────────────────────

def test_enrich_stream_no_jobs_emits_done(auth_client):
    repo = MagicMock()
    repo.find_by_stage.return_value = []
    with patch.object(enrich_router, "JobRepository", return_value=repo):
        resp = auth_client.get("/enrich/stream")
    assert resp.status_code == 200
    assert '"total": 0' in resp.text


def test_enrich_results(auth_client):
    repo = MagicMock()
    repo.find_by_stage.return_value = [_job({"domaine": "acme.io", "stage": "enriched"})]
    with patch.object(enrich_router, "JobRepository", return_value=repo):
        resp = auth_client.get("/enrich/results")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_enrich_company_found(auth_client):
    repo = MagicMock()
    job = MagicMock()
    job.model_dump.return_value = {"domaine": "acme.io", "nom": "Acme"}
    repo.find_one.return_value = job
    with patch.object(enrich_router, "JobRepository", return_value=repo):
        resp = auth_client.get("/enrich/company", params={"domaine": "acme.io"})
    assert resp.status_code == 200
    assert resp.json()["nom"] == "Acme"


def test_enrich_company_not_found_404(auth_client):
    repo = MagicMock()
    repo.find_one.return_value = None
    with patch.object(enrich_router, "JobRepository", return_value=repo):
        resp = auth_client.get("/enrich/company", params={"domaine": "ghost.io"})
    assert resp.status_code == 404
