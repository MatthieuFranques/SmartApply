"""Unit tests for prompt builders (pure string assembly)."""

from app.services import prompts


PROFILE = {
    "prenom_nom": "Jane Doe",
    "titre": "Fullstack Developer",
    "telephone": "0600000000",
    "email": "jane@doe.io",
    "portfolio": "https://jane.dev",
    "github": "https://github.com/jane",
    "diplome": "Master CS",
    "ecole": "EPITECH",
    "annee": "2024",
}


def test_build_header_includes_contact_and_links():
    header = prompts.build_header(PROFILE)
    assert "Jane Doe" in header
    assert "Fullstack Developer" in header
    assert "0600000000 | jane@doe.io" in header
    assert "Portfolio : https://jane.dev" in header
    assert "GitHub : https://github.com/jane" in header


def test_build_header_minimal_profile():
    header = prompts.build_header({"prenom_nom": "Solo"})
    assert header == "Solo"


def test_build_analysis_prompt_contains_company_and_candidate():
    company = {
        "nom": "Acme", "secteur": "IT", "ville": "Lyon",
        "tech_keywords": ["python", "react"], "job_offers": [],
    }
    out = prompts.build_analysis_prompt(company, PROFILE)
    assert "Acme" in out and "Lyon" in out
    assert "python, react" in out
    assert "Jane Doe" not in out  # header not part of analysis
    assert "Aucune offre parsée" in out


def test_build_analysis_prompt_with_cv_chunks():
    company = {"nom": "Acme", "secteur": "IT", "ville": "Lyon"}
    out = prompts.build_analysis_prompt(company, PROFILE, cv_chunks=["chunk A", "chunk B"])
    assert "EXTRAITS CV PERTINENTS" in out
    assert "chunk A" in out


def test_build_letter_prompt_targeted_vs_spontaneous():
    base = {"nom": "Acme", "secteur": "IT", "ville": "Lyon"}
    targeted = prompts.build_letter_prompt(
        {**base, "job_offers": [{"title": "Backend Dev", "url": "https://a/1", "tech_required": ["python"]}]},
        PROFILE, analysis="ANALYSE",
    )
    assert "Offre ciblée : Backend Dev" in targeted

    spontaneous = prompts.build_letter_prompt(base, PROFILE, analysis="ANALYSE")
    assert "candidature spontanée" in spontaneous


def test_build_letter_prompt_uses_rag_reference():
    out = prompts.build_letter_prompt(
        {"nom": "Acme", "secteur": "IT", "ville": "Lyon"},
        PROFILE, analysis="A",
        rag_context={"reference_letters": ["REF LETTER TEXT"]},
    )
    assert "LETTRE DE RÉFÉRENCE (RAG)" in out
    assert "REF LETTER TEXT" in out


def test_build_contact_form_prompt_lists_fields():
    company = {
        "nom": "Acme", "secteur": "IT", "ville": "Lyon",
        "contact_form": {
            "url": "https://acme.io/contact", "has_file_upload": True,
            "fields": [{"type": "text", "name": "name", "label": "Name"}],
        },
    }
    out = prompts.build_contact_form_prompt(company, PROFILE)
    assert "https://acme.io/contact" in out
    assert "name='name'" in out
    assert "Upload fichier possible : oui" in out
