"""Unit tests for the recruitment-email parser (candidature sync).

The Ollama call in `parse_email` is patched out so tests are deterministic and
offline: ignored emails return before any model call, and for the rest we force
the regex fallback path by making the Ollama helper raise.
"""

from unittest.mock import patch

import pytest

from app.services.job_applications import gmail_ollama_parser as parser


@pytest.fixture(autouse=True)
def _clear_cache():
    """Thread-local parse cache must not leak between tests."""
    parser.clear_cache()
    yield
    parser.clear_cache()


# ── status detection (regex) ──────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("nous avons le plaisir de vous offrir le poste", "Offre reçue"),
        ("congratulations, pleased to offer you", "Offre reçue"),
        ("nous souhaitons vous rencontrer en entretien", "Entretien"),
        ("we'd like to invite you for an interview", "Entretien"),
        ("malheureusement votre candidature n'a pas été retenue", "Refusé"),
        ("unfortunately we regret to inform you", "Refusé"),
        ("nous avons bien reçu votre candidature, en cours d'examen", "Décision requise"),
        ("we received your application and will review it", "Décision requise"),
        ("merci pour votre message", "En attente"),
    ],
)
def test_detect_statut_regex(text, expected):
    assert parser._detect_statut_regex(text) == expected


def test_statut_priority_offer_beats_interview():
    """Offer signal wins even when interview wording is also present."""
    text = "félicitation ! entretien prévu mais nous sommes heureux de vous proposer"
    assert parser._detect_statut_regex(text) == "Offre reçue"


# ── ignore detection ──────────────────────────────────────────

def test_ignored_automated_sender():
    reason = parser._is_ignored_regex("Sujet", "corps", "jobalerts-noreply@linkedin.com")
    assert reason == "Expéditeur automatique"


def test_ignored_job_alert_subject():
    reason = parser._is_ignored_regex("Des offres qui vous correspondent", "body", "x@acme.io")
    assert reason == "Email non-candidature"


def test_not_ignored_real_email():
    assert parser._is_ignored_regex("Votre entretien", "Bonjour", "hr@acme.io") is None


# ── status ambiguity ──────────────────────────────────────────

def test_ambiguous_only_for_long_pending():
    assert parser._statut_is_ambiguous("Refusé", "x" * 500) is False
    assert parser._statut_is_ambiguous("En attente", "short") is False
    assert parser._statut_is_ambiguous("En attente", "x" * 300) is True


# ── status upgrade priority ───────────────────────────────────

def test_should_upgrade_statut():
    assert parser.should_upgrade_statut("En attente", "Entretien") is True
    assert parser.should_upgrade_statut("Entretien", "Offre reçue") is True
    # never downgrade
    assert parser.should_upgrade_statut("Entretien", "En attente") is False
    assert parser.should_upgrade_statut("Offre reçue", "Refusé") is False
    # unknown status → no upgrade
    assert parser.should_upgrade_statut("Entretien", "Inconnu") is False


# ── parse_email end-to-end (Ollama patched) ───────────────────

def test_parse_email_ignored_returns_early():
    """Spam sender short-circuits before any Ollama call."""
    with patch.object(parser, "_ask_json") as mock_ask:
        result = parser.parse_email("noreply@indeed.com", "New jobs", "body")
    mock_ask.assert_not_called()
    assert result["ignorer"] is True
    assert result["raison_ignore"] == "Expéditeur automatique"


def test_parse_email_fallback_extracts_company_from_sender():
    """When Ollama fails, regex fallback derives company/status."""
    with patch.object(parser, "_ask_json", side_effect=RuntimeError("ollama down")):
        result = parser.parse_email(
            sender='"Acme Corp" <hr@acme.io>',
            subject="Entretien pour le poste de développeur",
            body="Nous souhaitons vous rencontrer en entretien.",
        )
    assert result["ignorer"] is False
    assert result["entreprise"] == "Acme Corp"
    assert result["statut"] == "Entretien"
    assert result["poste"]  # non-empty placeholder or extracted title


def test_parse_email_fallback_placeholders_when_unknown():
    with patch.object(parser, "_ask_json", side_effect=RuntimeError("down")):
        result = parser.parse_email("someone@gmail.com", "", "")
    assert result["entreprise"] == "Entreprise inconnue"
    assert result["poste"] == "Poste non précisé"


# ── public API + cache ────────────────────────────────────────

def test_public_api_uses_cache(monkeypatch):
    """Repeated public calls for the same email parse only once."""
    calls = {"n": 0}
    real_parse = parser.parse_email

    def counting_parse(sender, subject, body):
        calls["n"] += 1
        return real_parse(sender, subject, body)

    monkeypatch.setattr(parser, "parse_email", counting_parse)
    with patch.object(parser, "_ask_json", side_effect=RuntimeError("down")):
        parser.should_ignore("Sujet", "corps", "hr@acme.io")
        parser.extract_entreprise("hr@acme.io", "Sujet", "corps")
        parser.detect_statut("Sujet", "corps", "hr@acme.io")
    assert calls["n"] == 1


def test_should_ignore_returns_reason_for_spam():
    assert parser.should_ignore("Job alert", "body", "jobalerts@linkedin.com") is not None
