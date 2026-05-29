"""Unit tests for Adzuna job aggregation (country resolution + mapping + search)."""

from unittest.mock import MagicMock, patch

from app.services.jobs import adzuna


def test_resolve_country_known_and_default():
    assert adzuna._resolve_country("Paris, France") == "fr"
    assert adzuna._resolve_country("Brussels, Belgique") == "be"
    assert adzuna._resolve_country("London") == "gb"
    assert adzuna._resolve_country("somewhere unknown") == "fr"  # default


def test_map_job_complete():
    raw = {
        "redirect_url": "https://adzuna/job/1",
        "title": "Backend Developer",
        "company": {"display_name": "Acme"},
        "location": {"display_name": "Lyon"},
        "description": "x" * 800,
        "created": "2025-05-01T10:00:00Z",
    }
    out = adzuna._map_job(raw, "France")
    assert out["title"] == "Backend Developer"
    assert out["company"] == "Acme"
    assert out["location"] == "Lyon"
    assert out["date_posted"] == "2025-05-01"
    assert len(out["description"]) == 500  # truncated
    assert out["source"] == "indeed"
    assert out["id"]  # sha256 hash present


def test_map_job_without_url_is_skipped():
    assert adzuna._map_job({"title": "no url"}, "France") is None


def test_search_adzuna_no_credentials_returns_empty(monkeypatch):
    monkeypatch.setattr(adzuna, "_APP_ID", "")
    monkeypatch.setattr(adzuna, "_APP_KEY", "")
    assert adzuna.search_adzuna("python") == []


def test_search_adzuna_maps_results(monkeypatch):
    monkeypatch.setattr(adzuna, "_APP_ID", "id")
    monkeypatch.setattr(adzuna, "_APP_KEY", "key")
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "results": [
            {"redirect_url": "https://a/1", "title": "Dev"},
            {"title": "skipped, no url"},
        ]
    }
    with patch.object(adzuna, "requests") as mock_req:
        mock_req.get.return_value = resp
        out = adzuna.search_adzuna("python", "France", max_results=10)
    assert len(out) == 1
    assert out[0]["title"] == "Dev"


def test_search_adzuna_swallows_http_error(monkeypatch):
    monkeypatch.setattr(adzuna, "_APP_ID", "id")
    monkeypatch.setattr(adzuna, "_APP_KEY", "key")
    with patch.object(adzuna, "requests") as mock_req:
        mock_req.get.side_effect = RuntimeError("network")
        assert adzuna.search_adzuna("python") == []
