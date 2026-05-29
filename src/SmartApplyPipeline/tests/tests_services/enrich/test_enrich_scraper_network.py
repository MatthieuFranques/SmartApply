"""Tests for enrich_scraper network/offer helpers (requests mocked)."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from app.services.enrich import enrich_scraper as es
from app.services.enrich.enrich_config import JobOffer, ContactForm


def test_fetch_page_success():
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.text = "<html><body>Hi</body></html>"
    with patch.object(es.requests, "get", return_value=resp):
        soup = es.fetch_page("https://acme.io")
    assert isinstance(soup, BeautifulSoup)


def test_fetch_page_timeout_raises():
    with patch.object(es.requests, "get", side_effect=requests.exceptions.Timeout):
        with pytest.raises(TimeoutError):
            es.fetch_page("https://acme.io")


def test_fetch_page_request_error_raises_connection():
    with patch.object(es.requests, "get", side_effect=requests.exceptions.RequestException("x")):
        with pytest.raises(ConnectionError):
            es.fetch_page("https://acme.io")


def test_scrape_page_safe_swallows_errors():
    with patch.object(es, "fetch_page", side_effect=ConnectionError), \
         patch.object(es.time, "sleep"):
        assert es.scrape_page_safe("https://acme.io") is None


def test_scrape_page_safe_returns_soup():
    soup = BeautifulSoup("<p>x</p>", "html.parser")
    with patch.object(es, "fetch_page", return_value=soup), \
         patch.object(es.time, "sleep"):
        assert es.scrape_page_safe("https://acme.io") is soup


def test_extract_job_titles():
    text = "Développeur Backend | Data Engineer | Chef cuisinier"
    titles = es.extract_job_titles(text)
    assert any("Développeur" in t for t in titles)
    assert any("Engineer" in t for t in titles)


def test_scrape_job_offer_scores():
    soup = BeautifulSoup("<main>python react docker</main>", "html.parser")
    with patch.object(es, "scrape_page_safe", return_value=soup):
        offer = es.scrape_job_offer("https://a/1", "Backend Dev")
    assert isinstance(offer, JobOffer)
    assert offer.title == "Backend Dev"
    assert offer.relevance_score > 0


def test_scrape_job_offer_unreachable_returns_base():
    with patch.object(es, "scrape_page_safe", return_value=None):
        offer = es.scrape_job_offer("https://a/1", "Dev")
    assert offer.relevance_score == 0


def test_scrape_all_job_offers_sorts_and_filters():
    careers = BeautifulSoup("<a href='/jobs/1'>Dev</a>", "html.parser")
    o1 = JobOffer(title="Low", url="u1", relevance_score=2)
    o2 = JobOffer(title="High", url="u2", relevance_score=9)
    zero = JobOffer(title="Zero", url="u3", relevance_score=0)

    with patch.object(es, "extract_job_links", return_value=[{"title": "a", "url": "u1"},
                                                             {"title": "b", "url": "u2"},
                                                             {"title": "c", "url": "u3"}]), \
         patch.object(es, "scrape_job_offer", side_effect=[o1, o2, zero]):
        offers = es.scrape_all_job_offers(careers, "https://a/jobs")

    assert [o.title for o in offers] == ["High", "Low"]  # sorted desc, zero dropped


def test_find_contact_url_from_link():
    soup = BeautifulSoup("<a href='/contact'>Contact</a>", "html.parser")
    assert es.find_contact_url(soup, "https://acme.io") == "https://acme.io/contact"


def test_scrape_contact_info_no_url():
    soup = BeautifulSoup("<p>nothing</p>", "html.parser")
    with patch.object(es, "find_contact_url", return_value=None):
        form = es.scrape_contact_info(soup, "https://acme.io")
    assert isinstance(form, ContactForm)
    assert form.url == ""
