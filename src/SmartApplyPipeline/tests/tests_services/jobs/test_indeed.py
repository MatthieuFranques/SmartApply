"""Unit tests for Indeed/JSearch job aggregation (date param + mapping + search)."""

from unittest.mock import MagicMock, patch

from app.services.jobs import indeed_rss


def test_days_to_param_buckets():
    assert indeed_rss._days_to_param(1) == "today"
    assert indeed_rss._days_to_param(3) == "3days"
    assert indeed_rss._days_to_param(7) == "week"
    assert indeed_rss._days_to_param(30) == "month"


def test_map_job_builds_location():
    raw = {
        "job_apply_link": "https://js/1",
        "job_title": "Data Engineer",
        "employer_name": "Acme",
        "job_city": "Lille",
        "job_country": "France",
        "job_description": "y" * 700,
        "job_posted_at_datetime_utc": "2025-04-10T08:00:00Z",
    }
    out = indeed_rss._map_job(raw)
    assert out["title"] == "Data Engineer"
    assert out["location"] == "Lille, France"
    assert out["date_posted"] == "2025-04-10"
    assert len(out["description"]) == 500


def test_map_job_falls_back_to_google_link():
    raw = {"job_google_link": "https://g/2", "job_title": "Dev"}
    out = indeed_rss._map_job(raw)
    assert out["url"] == "https://g/2"


def test_map_job_no_link_skipped():
    assert indeed_rss._map_job({"job_title": "x"}) is None


def test_search_indeed_no_key_returns_empty(monkeypatch):
    monkeypatch.setattr(indeed_rss, "_API_KEY", "")
    assert indeed_rss.search_indeed("python") == []


def test_search_indeed_maps_results(monkeypatch):
    monkeypatch.setattr(indeed_rss, "_API_KEY", "key")
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"data": [{"job_apply_link": "https://js/1", "job_title": "Dev"}]}
    with patch.object(indeed_rss, "requests") as mock_req:
        mock_req.get.return_value = resp
        out = indeed_rss.search_indeed("python", max_results=10)
    assert len(out) == 1
    assert out[0]["title"] == "Dev"
