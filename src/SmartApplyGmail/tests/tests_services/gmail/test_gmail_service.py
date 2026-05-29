"""Unit tests for the Gmail service: parsing helpers, fetch, draft creation."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from app.services.gmail import gmail
from app.models.gmail import GmailMessage


# ── pure helpers ──────────────────────────────────────────────

def test_extract_links_finds_all_urls():
    text = "Apply here https://acme.io/jobs?id=1 or https://acme.io/about. Done."
    links = gmail._extract_links(text)
    assert "https://acme.io/jobs?id=1" in links
    assert "https://acme.io/about." in links or "https://acme.io/about" in links
    assert len(links) == 2


def test_extract_links_none():
    assert gmail._extract_links("no links here") == []


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


def test_decode_body_plain():
    payload = {"mimeType": "text/plain", "body": {"data": _b64("Hello world")}}
    assert gmail._decode_body(payload) == "Hello world"


def test_decode_body_recurses_into_parts():
    payload = {
        "mimeType": "multipart/alternative",
        "body": {},
        "parts": [
            {"mimeType": "text/html", "body": {"data": _b64("<p>ignored</p>")}},
            {"mimeType": "text/plain", "body": {"data": _b64("real body")}},
        ],
    }
    assert gmail._decode_body(payload) == "real body"


def test_parse_message_builds_model():
    raw = {
        "id": "msg_1",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Interview"},
                {"name": "From", "value": "Recruiter <hr@acme.io>"},
                {"name": "Date", "value": "Mon, 12 May 2025 10:00:00 +0000"},
            ],
            "body": {"data": _b64("See https://acme.io/call")},
        },
    }
    msg = gmail._parse_message(raw, "Candidatures")
    assert isinstance(msg, GmailMessage)
    assert msg.id == "msg_1"
    assert msg.subject == "Interview"
    assert msg.sender == "Recruiter <hr@acme.io>"
    assert msg.label == "Candidatures"
    assert msg.links == ["https://acme.io/call"]
    assert msg.received_at is not None


# ── draft creation ────────────────────────────────────────────

def test_create_gmail_draft_returns_id_and_url():
    fake_draft = {"id": "draft_99", "message": {"id": "m_77"}}
    service = MagicMock()
    service.users().drafts().create().execute.return_value = fake_draft

    with patch.object(gmail, "Credentials"), patch.object(gmail, "build", return_value=service):
        result = gmail.create_gmail_draft(
            access_token="tok", subject="Candidature", body="Bonjour", to="hr@acme.io"
        )

    assert result == {
        "draft_id": "draft_99",
        "draft_url": "https://mail.google.com/mail/#drafts/m_77",
    }


# ── fetch by label ────────────────────────────────────────────

def test_fetch_emails_by_label_resolves_id_and_parses():
    service = MagicMock()
    users = service.users.return_value
    users.labels().list().execute.return_value = {
        "labels": [{"id": "Label_5", "name": "Candidatures"}]
    }
    users.messages().list().execute.return_value = {"messages": [{"id": "msg_1"}]}
    users.messages().get().execute.return_value = {
        "id": "msg_1",
        "payload": {
            "mimeType": "text/plain",
            "headers": [{"name": "Subject", "value": "Hi"}],
            "body": {"data": _b64("body")},
        },
    }

    with patch.object(gmail, "Credentials"), patch.object(gmail, "build", return_value=service):
        emails = gmail.fetch_emails_by_label("Candidatures", "tok")

    assert len(emails) == 1
    assert emails[0].subject == "Hi"


def test_fetch_emails_by_label_unknown_label_raises():
    service = MagicMock()
    service.users().labels().list().execute.return_value = {"labels": []}

    with patch.object(gmail, "Credentials"), patch.object(gmail, "build", return_value=service):
        with pytest.raises(ValueError, match="introuvable"):
            gmail.fetch_emails_by_label("Nope", "tok")
