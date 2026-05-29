"""Unit tests for aggregating job offers out of enriched companies."""

from unittest.mock import MagicMock, patch

from app.services.jobs import from_pipeline


def _company(model_dict):
    m = MagicMock()
    m.model_dump.return_value = model_dict
    return m


def test_offers_extracted_and_sorted_by_relevance():
    companies = [
        _company({
            "nom": "Acme", "ville": "Lyon", "domaine": "acme.io", "secteur": "IT",
            "job_offers": [
                {"title": "Junior Dev", "url": "https://a/1", "relevance_score": 3,
                 "description": "d", "tech_required": ["python"]},
                {"title": "Senior Dev", "url": "https://a/2", "relevance_score": 9,
                 "description": "d", "tech_required": []},
            ],
        }),
    ]
    repo = MagicMock()
    repo.find_by_stage.return_value = companies

    with patch.object(from_pipeline, "JobRepository", return_value=repo):
        out = from_pipeline.get_offers_from_pipeline("user_1")

    assert [o["title"] for o in out] == ["Senior Dev", "Junior Dev"]  # sorted desc
    assert out[0]["company"] == "Acme"
    assert out[0]["source"] == "pipeline"
    repo.find_by_stage.assert_called_once_with("user_1", "enriched")


def test_offers_without_url_or_title_skipped():
    companies = [
        _company({
            "nom": "Acme", "ville": "", "domaine": "", "secteur": "",
            "job_offers": [
                {"title": "No URL", "url": "", "relevance_score": 5},
                {"title": "", "url": "https://a/3", "relevance_score": 5},
            ],
        }),
    ]
    repo = MagicMock()
    repo.find_by_stage.return_value = companies

    with patch.object(from_pipeline, "JobRepository", return_value=repo):
        out = from_pipeline.get_offers_from_pipeline("user_1")

    assert out == []


def test_no_companies_returns_empty():
    repo = MagicMock()
    repo.find_by_stage.return_value = []
    with patch.object(from_pipeline, "JobRepository", return_value=repo):
        assert from_pipeline.get_offers_from_pipeline("user_1") == []
