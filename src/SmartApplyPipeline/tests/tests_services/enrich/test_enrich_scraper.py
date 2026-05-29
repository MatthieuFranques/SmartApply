"""Unit tests for enrich extraction helpers (pure parsing, no network)."""

from bs4 import BeautifulSoup

from app.services.enrich import enrich_scraper as es


# ── URL helpers ───────────────────────────────────────────────

def test_build_url_adds_scheme():
    assert es.build_url("acme.io") == "https://acme.io"
    assert es.build_url("https://acme.io") == "https://acme.io"
    assert es.build_url("  ") == ""


def test_resolve_url_relative():
    assert es.resolve_url("/jobs", "https://acme.io/about") == "https://acme.io/jobs"


# ── keyword detection ─────────────────────────────────────────

def test_detect_tech_keywords():
    found = es.detect_tech_keywords("We use Python, React and Docker daily")
    assert "python" in found and "react" in found and "docker" in found


def test_detect_size_hint():
    assert es.detect_size_hint("Nous sommes une startup en croissance") == "Startup"
    assert es.detect_size_hint("texte neutre") == ""


def test_detect_founded_year():
    assert es.detect_founded_year("Société fondée en 2015 à Lyon") == "2015"
    assert es.detect_founded_year("founded in 2008") == "2008"
    assert es.detect_founded_year("no year here") == ""


def test_score_offer_relevance_bounded():
    score = es.score_offer_relevance("Poste React TypeScript Docker Python AWS", [])
    assert 0 < score <= 10
    assert es.score_offer_relevance("texte sans techno", []) == 0


# ── text extraction ───────────────────────────────────────────

def test_extract_meta_description():
    soup = BeautifulSoup('<meta name="description" content="Best agency">', "html.parser")
    assert es.extract_meta_description(soup) == "Best agency"


def test_extract_meta_description_og_fallback():
    soup = BeautifulSoup('<meta property="og:description" content="OG desc">', "html.parser")
    assert es.extract_meta_description(soup) == "OG desc"


def test_extract_main_text_strips_scripts():
    html = "<main><script>var x=1;</script><p>Hello world content here</p></main>"
    soup = BeautifulSoup(html, "html.parser")
    text = es.extract_main_text(soup)
    assert "Hello world content here" in text
    assert "var x" not in text


def test_extract_key_phrases_length_filter():
    text = "Short. " + ("A sentence that is reasonably long enough to keep. ") + "Hi."
    phrases = es.extract_key_phrases(text)
    assert any("reasonably long enough" in p for p in phrases)
    assert all(30 < len(p) < 180 for p in phrases)


def test_find_about_url():
    html = '<a href="/about-us">About us</a>'
    soup = BeautifulSoup(html, "html.parser")
    assert es.find_about_url(soup, "https://acme.io") == "https://acme.io/about-us"


# ── job links + contact form ──────────────────────────────────

def test_extract_job_links():
    html = """
      <a href="/careers/dev">Développeur Backend</a>
      <a href="/about">About</a>
      <a href="/jobs/data">Data Engineer</a>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = es.extract_job_links(soup, "https://acme.io")
    urls = {l["url"] for l in links}
    assert "https://acme.io/careers/dev" in urls
    assert "https://acme.io/jobs/data" in urls
    assert "https://acme.io/about" not in urls


def test_extract_contact_form_detects_file_upload_and_email():
    html = """
      <p>Contact: hello@acme.io</p>
      <form>
        <input type="text" name="name"/>
        <textarea name="message"></textarea>
        <input type="file" name="cv"/>
        <input type="submit" value="Send"/>
      </form>
    """
    soup = BeautifulSoup(html, "html.parser")
    form = es.extract_contact_form(soup, "https://acme.io/contact")
    assert form.email_found == "hello@acme.io"
    assert form.has_file_upload is True
    field_types = {f["type"] for f in form.fields}
    assert "file" in field_types and "textarea" in field_types
