"""Unit tests for company scraping: mapping, dedup, full scrape orchestration."""

from unittest.mock import patch

from app.services.scraping import scraper


def test_fetch_company_data_maps_fields():
    out = scraper.fetch_company_data(
        {"domain": "acme.io", "organization": "Acme"}, "IT services", "Lyon"
    )
    assert out == {
        "nom": "Acme", "domaine": "acme.io", "ville": "Lyon",
        "email": "", "secteur": "IT services",
    }


def test_fetch_company_data_falls_back_to_domain_as_name():
    out = scraper.fetch_company_data({"domain": "acme.io"}, "IT", "Lyon")
    assert out["nom"] == "acme.io"


def test_fetch_company_data_no_domain_returns_none():
    assert scraper.fetch_company_data({"organization": "Acme"}, "IT", "Lyon") is None


def test_deduplicate_removes_dupes_and_respects_global_seen():
    raw = [
        {"domain": "a.io"}, {"domain": "a.io"}, {"domain": "b.io"}, {"domain": ""},
    ]
    out = scraper._deduplicate(raw, global_seen={"b.io"})
    domains = [c["domain"] for c in out]
    assert domains == ["a.io"]  # dupe + already-seen b.io + empty all dropped


def test_scrape_companies_dedupes_across_cities():
    # Same domain returned for two cities → counted once
    def fake_discover(sector, city, max_results, keyword_match):
        return [{"domain": "acme.io", "organization": "Acme"}]

    with patch.object(scraper, "discover_companies", side_effect=fake_discover):
        out = scraper.scrape_companies("IT", ["Lyon", "Paris"], max_results=10)

    assert len(out) == 1
    assert out[0]["domaine"] == "acme.io"
