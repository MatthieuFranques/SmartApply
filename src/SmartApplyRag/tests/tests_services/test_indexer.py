"""Unit tests for indexing (slug, letter/CV/company/reference upserts)."""

from unittest.mock import patch

from app.services import indexer


def test_slug_normalizes():
    assert indexer._slug("Acme Corp! (Lyon)") == "acme_corp_lyon"
    assert indexer._slug("  Hello  World  ") == "hello_world"


def test_index_letter_builds_id_and_metadata():
    company = {"nom": "Acme Corp", "secteur": "IT", "ville": "Lyon", "tech_keywords": ["python"]}
    with patch.object(indexer, "upsert") as mock_upsert:
        doc_id = indexer.index_letter("Dear...", company, "letter_targeted", user_id="u1")

    assert doc_id.startswith("u1_acme_corp_")
    args, _ = mock_upsert.call_args
    collection, passed_id, text, metadata = args
    assert collection == "letters"
    assert text == "Dear..."
    assert metadata["company_name"] == "Acme Corp"
    assert metadata["mode"] == "letter_targeted"
    assert metadata["user_id"] == "u1"


def test_index_cv_profile_skips_empty_chunks():
    profile = {
        "experiences": "5 ans en dev",
        "projet_phare": "",          # skipped
        "competences": "Python, SQL",
        "soft_skills": "", "recherche": "",  # combined empty → skipped
        "prenom_nom": "Jane",
    }
    with patch.object(indexer, "upsert") as mock_upsert:
        ids = indexer.index_cv_profile(profile, user_id="u1")

    assert "u1_cv_experiences" in ids
    assert "u1_cv_skills" in ids
    assert "u1_cv_project" not in ids
    assert mock_upsert.call_count == 2


def test_index_company_returns_slug():
    company = {"nom": "Acme", "secteur": "IT", "description": "We build software"}
    with patch.object(indexer, "upsert") as mock_upsert:
        slug = indexer.index_company(company)
    assert slug == "acme"
    mock_upsert.assert_called_once()


def test_index_reference_letter():
    with patch.object(indexer, "upsert") as mock_upsert:
        doc_id = indexer.index_reference_letter("ref text", "linkedin")
    assert doc_id.startswith("ref_linkedin_")
    mock_upsert.assert_called_once()
