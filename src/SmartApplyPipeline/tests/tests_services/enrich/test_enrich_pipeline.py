"""Tests for enrich_company orchestration + summarize_context (scraper mocked)."""

from unittest.mock import MagicMock, patch

from app.services.enrich import enrich_pipeline as ep
from app.services.enrich.enrich_config import CompanyContext, JobOffer, ContactForm


def test_enrich_company_empty_domain_errors():
    with patch.object(ep, "build_url", return_value=""):
        ctx = ep.enrich_company({"nom": "A", "domaine": ""})
    assert ctx.scrape_status == "error"
    assert ctx.scrape_error == "Domaine vide"


def test_enrich_company_with_offers():
    soup = MagicMock()
    offer = JobOffer(title="Dev", url="https://a/1", relevance_score=8)

    with patch.object(ep, "build_url", return_value="https://acme.io"), \
         patch.object(ep, "fetch_page", return_value=soup), \
         patch.object(ep, "extract_main_text", return_value="python react"), \
         patch.object(ep, "extract_meta_description", return_value="desc"), \
         patch.object(ep, "detect_tech_keywords", return_value=["python"]), \
         patch.object(ep, "detect_size_hint", return_value="Startup"), \
         patch.object(ep, "extract_key_phrases", return_value=["phrase"]), \
         patch.object(ep, "detect_founded_year", return_value="2015"), \
         patch.object(ep, "find_about_url", return_value=None), \
         patch.object(ep, "extract_job_titles", return_value=["Dev"]), \
         patch.object(ep, "scrape_page_safe", return_value=soup), \
         patch.object(ep, "scrape_all_job_offers", return_value=[offer]):
        ctx = ep.enrich_company({"nom": "Acme", "domaine": "acme.io", "careers_url": "https://acme.io/jobs"})

    assert ctx.scrape_status == "ok"
    assert ctx.description == "desc"
    assert ctx.is_recruiting is True
    assert ctx.job_offers and ctx.job_offers[0]["title"] == "Dev"


def test_enrich_company_no_offers_falls_back_to_contact():
    soup = MagicMock()
    contact = ContactForm(url="https://acme.io/contact", email_found="hi@acme.io")

    with patch.object(ep, "build_url", return_value="https://acme.io"), \
         patch.object(ep, "fetch_page", return_value=soup), \
         patch.object(ep, "extract_main_text", return_value="text"), \
         patch.object(ep, "extract_meta_description", return_value=""), \
         patch.object(ep, "detect_tech_keywords", return_value=[]), \
         patch.object(ep, "detect_size_hint", return_value=""), \
         patch.object(ep, "extract_key_phrases", return_value=[]), \
         patch.object(ep, "detect_founded_year", return_value=""), \
         patch.object(ep, "find_about_url", return_value=None), \
         patch.object(ep, "scrape_contact_info", return_value=contact):
        ctx = ep.enrich_company({"nom": "Acme", "domaine": "acme.io"})  # no careers_url

    assert ctx.scrape_status == "ok"
    assert ctx.contact_form["email_found"] == "hi@acme.io"


def test_enrich_company_handles_timeout():
    with patch.object(ep, "build_url", return_value="https://acme.io"), \
         patch.object(ep, "fetch_page", side_effect=TimeoutError("slow")):
        ctx = ep.enrich_company({"nom": "Acme", "domaine": "acme.io"})
    assert ctx.scrape_status == "timeout"


def test_summarize_context_variants():
    ctx = CompanyContext(nom="Acme", domaine="a", ville="", secteur="")
    ctx.tech_keywords = ["python", "react"]
    ctx.job_offers = [{"relevance_score": 8}, {"relevance_score": 5}]
    ctx.contact_form = {"has_file_upload": True}
    out = ep.summarize_context(ctx)
    assert "Acme" in out and "2 tech" in out and "meilleure: 8/10" in out and "contact: oui" in out

    ctx2 = CompanyContext(nom="B", domaine="b", ville="", secteur="")
    ctx2.is_recruiting = True
    assert "recrute mais offres non parsées" in ep.summarize_context(ctx2)
