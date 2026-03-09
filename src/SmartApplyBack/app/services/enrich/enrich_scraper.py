# ============================================================
# enrich_scraper.py
# Fonctions de scraping et d'extraction
# ============================================================

import re
import time
from typing import Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from enrich_config import (
    HEADERS, TIMEOUT,
    TECH_KEYWORDS, SIZE_HINTS, JOB_TITLE_KEYWORDS,
    CANDIDATE_KEYWORDS, CONTACT_PATHS,
    JobOffer, ContactForm,
)


# ── Utilitaires de base ─────────────────────────────────────

def build_url(domaine: str) -> str:
    domaine = domaine.strip()
    if not domaine:
        return ""
    if not domaine.startswith("http"):
        return f"https://{domaine}"
    return domaine


def fetch_page(url: str) -> BeautifulSoup:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Timeout sur {url}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(str(e))


def scrape_page_safe(url: str, delay: float = 0.5) -> Optional[BeautifulSoup]:
    """Scrape avec délai et gestion d'erreur silencieuse."""
    time.sleep(delay)
    try:
        return fetch_page(url)
    except Exception:
        return None


def resolve_url(href: str, base_url: str) -> str:
    """Transforme un href relatif en URL absolue."""
    return urljoin(base_url, href)


# ── Extraction générique ────────────────────────────────────

def extract_meta_description(soup: BeautifulSoup) -> str:
    for attrs in [{"name": "description"}, {"property": "og:description"}]:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def extract_main_text(soup: BeautifulSoup, max_chars: int = 3000) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|main|body", re.I))
    )
    target = main if main else soup.body
    if not target:
        return ""
    text = target.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)[:max_chars]


def find_about_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    patterns = re.compile(r"(about|qui|propos|nous|company|entreprise|story)", re.I)
    for a in soup.find_all("a", href=True):
        href, text = a["href"], a.get_text(strip=True)
        if patterns.search(href) or patterns.search(text):
            return resolve_url(href, base_url)
    return None


# ── Détection de mots-clés ──────────────────────────────────

def detect_tech_keywords(text: str) -> list:
    text_lower = text.lower()
    return [kw for kw in TECH_KEYWORDS if kw in text_lower]


def detect_size_hint(text: str) -> str:
    text_lower = text.lower()
    for kw, label in SIZE_HINTS.items():
        if kw in text_lower:
            return label
    return ""


def detect_founded_year(text: str) -> str:
    patterns = [
        r"fond[eé][e]?\s+en\s+(20\d{2}|19\d{2})",
        r"founded\s+in\s+(20\d{2}|19\d{2})",
        r"cr[eé][eé][e]?\s+en\s+(20\d{2}|19\d{2})",
        r"since\s+(20\d{2}|19\d{2})",
        r"depuis\s+(20\d{2}|19\d{2})",
        r"established\s+in\s+(20\d{2}|19\d{2})",
        r"©\s*(20\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    return ""


def extract_key_phrases(text: str, max_phrases: int = 5) -> list:
    sentences = re.split(r"[.!?]\s+", text)
    phrases = []
    for s in sentences:
        s = s.strip()
        if 30 < len(s) < 180:
            phrases.append(s)
        if len(phrases) >= max_phrases:
            break
    return phrases


def extract_job_titles(text: str) -> list:
    """Extrait les intitulés de postes depuis la page carrières."""
    titles, seen = [], set()
    candidates = re.split(r"[\n\r|•·–—]", text)
    candidates += re.split(r"[.!?]\s+", text)
    for candidate in candidates:
        candidate = candidate.strip()
        if not (5 < len(candidate) < 80):
            continue
        for kw in JOB_TITLE_KEYWORDS:
            if kw in candidate.lower():
                clean = re.sub(r"\s+", " ", candidate).strip()
                if clean.lower() not in seen:
                    seen.add(clean.lower())
                    titles.append(clean)
                break
    return titles[:8]


# ── Extraction des offres d'emploi ──────────────────────────

def score_offer_relevance(text: str, tech_required: list) -> int:
    """
    Score de pertinence d'une offre vs le profil candidat (0-10).
    Basé sur les CANDIDATE_KEYWORDS présents dans l'offre.
    """
    text_lower = text.lower()
    matches = sum(1 for kw in CANDIDATE_KEYWORDS if kw in text_lower)
    # Bonus si les technos requises matchent le profil
    tech_matches = sum(1 for t in tech_required if t in CANDIDATE_KEYWORDS)
    score = min(matches + tech_matches, 10)
    return score


def extract_job_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Détecte les liens vers des offres individuelles sur une page carrières.
    Retourne une liste de {title, url}.
    """
    job_pattern = re.compile(
        r"(job|offre|poste|career|emploi|position|recrutement|vacancy|opening)",
        re.I
    )
    title_pattern = re.compile(
        "|".join(JOB_TITLE_KEYWORDS), re.I
    )

    found, seen = [], set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)

        if not text or len(text) > 100:
            continue

        # Le lien ou le texte doit ressembler à une offre
        if not (job_pattern.search(href) or title_pattern.search(text)):
            continue

        full_url = resolve_url(href, base_url)
        if full_url in seen:
            continue

        seen.add(full_url)
        found.append({"title": text, "url": full_url})

    return found[:15]  # Max 15 offres à explorer


def scrape_job_offer(url: str, title: str) -> JobOffer:
    """
    Scrape une offre d'emploi individuelle.
    Extrait description complète + technologies requises + score.
    """
    offer = JobOffer(title=title, url=url)

    soup = scrape_page_safe(url, delay=0.3)
    if not soup:
        return offer

    description = extract_main_text(soup, max_chars=2000)
    offer.description    = description
    offer.tech_required  = detect_tech_keywords(description)
    offer.relevance_score = score_offer_relevance(description, offer.tech_required)

    return offer


def scrape_all_job_offers(careers_soup: BeautifulSoup, careers_url: str) -> list[JobOffer]:
    """
    Pipeline complet :
    1. Détecte les liens vers les offres sur la page carrières
    2. Scrape chaque offre individuellement
    3. Trie par pertinence décroissante
    4. Retourne uniquement les offres avec score > 0
    """
    job_links = extract_job_links(careers_soup, careers_url)

    if not job_links:
        return []

    offers = []
    for link in job_links:
        offer = scrape_job_offer(link["url"], link["title"])
        if offer.relevance_score > 0:
            offers.append(offer)

    # Trie par pertinence décroissante
    offers.sort(key=lambda o: o.relevance_score, reverse=True)
    return offers


# ── Détection du formulaire de contact ─────────────────────

def find_contact_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Cherche une page de contact depuis le menu/footer."""
    pattern = re.compile(r"(contact|nous[\s-]?contacter|get[\s-]?in[\s-]?touch)", re.I)
    for a in soup.find_all("a", href=True):
        href, text = a["href"], a.get_text(strip=True)
        if pattern.search(href) or pattern.search(text):
            return resolve_url(href, base_url)

    # Essaie les chemins standards
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    for path in CONTACT_PATHS:
        url = f"{base}{path}"
        try:
            resp = requests.head(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                return url
        except Exception:
            continue
    return None


def extract_contact_form(soup: BeautifulSoup, url: str) -> ContactForm:
    """
    Analyse un formulaire de contact :
    - Champs présents (nom, email, message, etc.)
    - Présence d'un input file (upload CV/portfolio)
    - Email de contact direct dans le texte
    """
    form = ContactForm(url=url)

    # Cherche un email direct dans la page
    text = soup.get_text()
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if email_match:
        form.email_found = email_match.group(0)

    # Analyse le formulaire HTML
    html_form = soup.find("form")
    if not html_form:
        return form

    fields = []
    for inp in html_form.find_all(["input", "textarea", "select"]):
        input_type = inp.get("type", "text").lower()
        name       = inp.get("name", "") or inp.get("placeholder", "") or inp.get("id", "")

        if input_type == "file":
            form.has_file_upload = True
            fields.append({"type": "file", "name": name, "label": "Upload fichier (CV/Portfolio)"})
        elif input_type in ("submit", "button", "hidden", "csrf"):
            continue
        elif inp.name == "textarea":
            fields.append({"type": "textarea", "name": name, "label": "Message"})
        else:
            fields.append({"type": input_type, "name": name, "label": name})

    form.fields = fields
    return form


def scrape_contact_info(main_soup: BeautifulSoup, base_url: str) -> ContactForm:
    """
    Pipeline de récupération du formulaire de contact :
    1. Cherche l'URL de la page contact
    2. Scrape et analyse le formulaire
    """
    contact_url = find_contact_url(main_soup, base_url)
    if not contact_url:
        return ContactForm()

    contact_soup = scrape_page_safe(contact_url, delay=0.3)
    if not contact_soup:
        return ContactForm(url=contact_url)

    return extract_contact_form(contact_soup, contact_url)