"""Router tests for RAG endpoints (services mocked)."""

from unittest.mock import patch

from app.routers import generate as generate_router
from app.routers import retrieve as retrieve_router
from app.routers import ingest as ingest_router
from app.services import indexer


# ── /generate ─────────────────────────────────────────────────

def test_generate_letter_success(client):
    with patch.object(generate_router, "determine_mode", return_value="letter"), \
         patch.object(generate_router, "generate_letter", return_value="Dear Acme..."):
        resp = client.post("/generate/letter", json={
            "company": {"nom": "Acme", "job_offers": [{"title": "Dev"}]},
            "profile": {}, "model": "mistral",
        })
    assert resp.status_code == 200
    body = resp.json()
    assert body["letter"] == "Dear Acme..."
    assert body["mode"] == "letter_targeted"


def test_generate_letter_contact_mode_returns_400(client):
    with patch.object(generate_router, "determine_mode", return_value="contact"):
        resp = client.post("/generate/letter", json={
            "company": {"nom": "Acme"}, "profile": {},
        })
    assert resp.status_code == 400


def test_generate_letter_failure_returns_503(client):
    with patch.object(generate_router, "determine_mode", return_value="letter"), \
         patch.object(generate_router, "generate_letter", side_effect=RuntimeError("ollama down")):
        resp = client.post("/generate/letter", json={"company": {"nom": "Acme"}, "profile": {}})
    assert resp.status_code == 503


def test_generate_contact_success(client):
    with patch.object(generate_router, "generate_contact_form", return_value={"objet": "x"}):
        resp = client.post("/generate/contact", json={"company": {"nom": "Acme"}, "profile": {}})
    assert resp.status_code == 200
    assert resp.json() == {"objet": "x"}


# ── /index ────────────────────────────────────────────────────

def test_index_letter(client):
    with patch.object(indexer, "index_letter", return_value="doc_1"):
        resp = client.post("/index/letter", json={
            "letter_text": "txt", "company": {"nom": "Acme"}, "mode": "letter", "user_id": "u1",
        })
    assert resp.status_code == 201
    assert resp.json()["doc_ids"] == ["doc_1"]


def test_index_cv(client):
    with patch.object(indexer, "index_cv_profile", return_value=["u1_cv_x"]):
        resp = client.post("/index/cv", json={"profile": {"experiences": "x"}, "user_id": "u1"})
    assert resp.status_code == 201


def test_index_company(client):
    with patch.object(indexer, "index_company", return_value="acme"):
        resp = client.post("/index/company", json={"company": {"nom": "Acme"}})
    assert resp.status_code == 201


def test_index_reference(client):
    with patch.object(indexer, "index_reference_letter", return_value="ref_1"):
        resp = client.post("/index/reference", json={"letter_text": "t", "source": "linkedin"})
    assert resp.status_code == 201


def test_index_error_returns_500(client):
    with patch.object(indexer, "index_company", side_effect=RuntimeError("boom")):
        resp = client.post("/index/company", json={"company": {"nom": "Acme"}})
    assert resp.status_code == 500


# ── /retrieve ─────────────────────────────────────────────────

def test_retrieve_context(client):
    ctx = {"similar_letters": ["l1"], "cv_chunks": [], "reference_letters": [], "has_context": True}
    with patch.object(retrieve_router, "get_letter_context", return_value=ctx):
        resp = client.post("/retrieve/context", json={"company": {"nom": "Acme"}})
    assert resp.status_code == 200
    assert resp.json()["has_context"] is True


# ── /ingest ───────────────────────────────────────────────────

def test_trigger_ingest(client):
    out = {"cvs": [], "letters": [], "errors": []}
    with patch.object(ingest_router, "ingest_inbox", return_value=out):
        resp = client.post("/ingest/")
    assert resp.status_code == 200
    assert resp.json() == out


def test_ingest_status(client):
    resp = client.get("/ingest/status")
    assert resp.status_code == 200
    assert "total" in resp.json()
