"""Router tests for /gmail (messages list, draft creation)."""

from unittest.mock import patch

from app.routers import gmail as gmail_router
from app.models.gmail import GmailMessage


def test_get_messages_success(auth_client):
    msgs = [GmailMessage(id="1", subject="Hi", sender="hr@acme.io")]
    with patch.object(gmail_router, "fetch_emails_by_label", return_value=msgs):
        resp = auth_client.get("/gmail/messages")
    assert resp.status_code == 200
    assert resp.json()[0]["subject"] == "Hi"


def test_get_messages_service_error_returns_500(auth_client):
    with patch.object(gmail_router, "fetch_emails_by_label", side_effect=RuntimeError("token")):
        resp = auth_client.get("/gmail/messages")
    assert resp.status_code == 500


def test_create_draft_company_not_found_returns_404(auth_client):
    with patch.object(gmail_router, "_get_company", return_value=None):
        resp = auth_client.post("/gmail/draft", json={"domaine": "acme.io", "model": "mistral"})
    assert resp.status_code == 404


def test_create_draft_success_letter_mode(auth_client):
    company = {
        "nom": "Acme", "job_offers": [{"title": "Backend Dev"}], "contact_form": {},
    }
    with patch.object(gmail_router, "_get_company", return_value=company), \
         patch.object(gmail_router, "_call_rag", return_value={"letter": "Dear Acme..."}), \
         patch.object(gmail_router, "create_gmail_draft",
                      return_value={"draft_id": "d1", "draft_url": "https://mail/d1"}):
        resp = auth_client.post("/gmail/draft", json={"domaine": "acme.io", "model": "mistral"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["draft_id"] == "d1"
    assert "Backend Dev" in data["subject"]


def test_create_draft_rag_unavailable_returns_503(auth_client):
    company = {"nom": "Acme", "job_offers": [{"title": "Dev"}], "contact_form": {}}
    with patch.object(gmail_router, "_get_company", return_value=company), \
         patch.object(gmail_router, "_call_rag", side_effect=RuntimeError("rag down")):
        resp = auth_client.post("/gmail/draft", json={"domaine": "acme.io", "model": "mistral"})
    assert resp.status_code == 503


def test_determine_mode_helper():
    assert gmail_router._determine_mode({"job_offers": [1]}) == "letter"
    assert gmail_router._determine_mode({"contact_form": {"x": 1}}) == "contact"
    assert gmail_router._determine_mode({}) == "letter"
