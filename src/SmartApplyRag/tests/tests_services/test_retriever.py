"""Unit tests for retrieval (query building + context assembly)."""

from unittest.mock import patch

from app.services import retriever


COMPANY = {
    "nom": "Acme", "secteur": "IT", "ville": "Lyon",
    "tech_keywords": ["python", "react"],
    "job_keywords": ["backend"],
    "description": "We build software " * 50,
}


def test_company_query_includes_identity_and_truncates_description():
    q = retriever._company_query(COMPANY)
    assert "Acme" in q and "IT" in q and "Lyon" in q
    assert "python" in q and "react" in q


def test_tech_query_focuses_on_stack():
    q = retriever._tech_query(COMPANY)
    assert "python" in q and "backend" in q
    assert "Acme" not in q  # company name excluded from tech query


def test_get_similar_letters_unwraps_text():
    fake = [{"text": "letter 1", "metadata": {}, "distance": 0.1}]
    with patch.object(retriever, "query", return_value=fake) as mock_q:
        out = retriever.get_similar_letters(COMPANY, k=3)
    assert out == ["letter 1"]
    mock_q.assert_called_once()


def test_get_letter_context_aggregates_all_sources():
    def fake_query(collection, text, k):
        return [{"text": f"{collection}_doc"}]

    with patch.object(retriever, "query", side_effect=fake_query):
        ctx = retriever.get_letter_context(COMPANY)

    assert ctx["similar_letters"] == ["letters_doc"]
    assert ctx["cv_chunks"] == ["cv_chunks_doc"]
    assert ctx["reference_letters"] == ["references_doc"]
    assert ctx["has_context"] is True


def test_get_letter_context_empty_has_no_context():
    with patch.object(retriever, "query", return_value=[]):
        ctx = retriever.get_letter_context(COMPANY)
    assert ctx["has_context"] is False
