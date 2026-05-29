"""Unit tests for generation (mode selection, letter assembly, contact form JSON)."""

from unittest.mock import patch

from app.services import generator


PROFILE = {"prenom_nom": "Jane Doe", "email": "jane@doe.io"}


# ── mode selection ────────────────────────────────────────────

def test_determine_mode():
    assert generator.determine_mode({"job_offers": [{"title": "x"}]}) == "letter"
    assert generator.determine_mode({"contact_form": {"url": "x"}}) == "contact"
    assert generator.determine_mode({}) == "letter"


# ── letter generation ─────────────────────────────────────────

def test_generate_letter_assembles_header_and_body():
    company = {"nom": "Acme", "secteur": "IT", "ville": "Lyon"}
    with patch.object(generator, "get_letter_context", return_value={}), \
         patch.object(generator, "index_letter"), \
         patch.object(generator, "_chat", side_effect=["ANALYSIS", "LETTER BODY"]) as mock_chat:
        letter = generator.generate_letter(company, PROFILE, model="mistral")

    assert "Jane Doe" in letter          # header
    assert "LETTER BODY" in letter       # body
    assert mock_chat.call_count == 2     # analysis pass + letter pass


def test_generate_letter_survives_rag_and_index_failures():
    company = {"nom": "Acme", "secteur": "IT", "ville": "Lyon"}
    with patch.object(generator, "get_letter_context", side_effect=RuntimeError("chroma down")), \
         patch.object(generator, "index_letter", side_effect=RuntimeError("index down")), \
         patch.object(generator, "_chat", side_effect=["ANALYSIS", "BODY"]):
        letter = generator.generate_letter(company, PROFILE, model="mistral")
    assert "BODY" in letter  # generation still completes


# ── contact form generation ───────────────────────────────────

def test_generate_contact_form_parses_json():
    company = {"nom": "Acme", "secteur": "IT", "ville": "Lyon", "contact_form": {}}
    raw = '```json\n{"objet": "Candidature", "message": "Bonjour"}\n```'
    with patch.object(generator, "_chat", return_value=raw):
        out = generator.generate_contact_form(company, PROFILE, model="mistral")
    assert out == {"objet": "Candidature", "message": "Bonjour"}


def test_generate_contact_form_invalid_json_fallback():
    company = {"nom": "Acme", "secteur": "IT", "ville": "Lyon", "contact_form": {}}
    with patch.object(generator, "_chat", return_value="not json at all"):
        out = generator.generate_contact_form(company, PROFILE, model="mistral")
    assert "error" in out
    assert out["raw_response"] == "not json at all"
