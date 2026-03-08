"""
prefilter.py
------------
Prétraitement GRATUIT des entreprises avant le deep filter.
Élimine les entreprises hors cible sans consommer de crédits API.

Pipeline :
    1. Vérifie que le domaine DNS existe
    2. Scrape titre + meta description + keywords de la page d'accueil
    3. Filtre les mots blacklistés (hors secteur IT)
    4. Détecte les mots-clés IT positifs
    5. Attribue un pré-score pour prioriser le deep filter

Usage :
    python prefilter.py
    python prefilter.py --input entreprises_toulouse.csv --output results/prefiltered.csv
"""

import os
import sys
import time
import socket
import argparse
import requests

sys.path.insert(0, os.path.dirname(__file__))

from bs4             import BeautifulSoup
from dotenv          import load_dotenv
from filter_config   import TIMEOUT_HTTP, PAUSE, MIN_PRESCORE, HTTP_HEADERS
from filter_csv      import load_csv, save_csv, PREFILTER_FIELDS, ELIMINATED_FIELDS
from filter_scoring  import detect_blacklist, count_it_keywords, compute_prescore

load_dotenv()

DEFAULT_INPUT  = os.getenv("CSV_OUTPUT_FILE", "entreprises.csv")
DEFAULT_OUTPUT = "entreprises_prefiltered.csv"


# ─── VÉRIFICATIONS RÉSEAU ────────────────────────────────────

def check_domain_dns(domain: str) -> bool:
    """Vérifie que le domaine résout en IP via DNS. Élimine les domaines fantômes."""
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False


def fetch_site_content(domain: str) -> dict:
    """
    Récupère titre + meta description + keywords de la page d'accueil.
    Essaie https:// puis http:// en fallback.
    Retourne accessible=False si le site est injoignable.
    """
    for scheme in ["https://", "http://"]:
        try:
            response = requests.get(
                f"{scheme}{domain}",
                timeout         = TIMEOUT_HTTP,
                allow_redirects = True,
                headers         = HTTP_HEADERS,
            )
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            title  = soup.title.string.strip() if soup.title else ""

            meta   = soup.find("meta", attrs={"name": "description"})
            desc   = meta["content"].strip() if meta and meta.get("content") else ""

            kw_tag = soup.find("meta", attrs={"name": "keywords"})
            kw     = kw_tag["content"].strip() if kw_tag and kw_tag.get("content") else ""

            return {
                "accessible" : True,
                "title"      : title[:200],
                "description": desc[:300],
                "keywords"   : kw[:200],
            }

        except requests.exceptions.SSLError:
            continue
        except Exception:
            continue

    return {"accessible": False, "title": "", "description": "", "keywords": ""}


# ─── PIPELINE PRÉFILTRAGE ────────────────────────────────────

def prefilter_companies(companies: list, min_prescore: int = MIN_PRESCORE) -> tuple:
    """
    Applique le pipeline complet sur toutes les entreprises.
    Retourne (à_scorer, éliminées).
    """
    to_score   = []
    eliminated = []
    total      = len(companies)

    for i, company in enumerate(companies, 1):
        domain = company.get("domaine", "")
        name   = company.get("nom", "?")
        print(f"  🔍 [{i}/{total}] {name} ({domain})...")

        # 1. DNS
        if not check_domain_dns(domain):
            print(f"      ❌ DNS invalide")
            eliminated.append({**company, "prescore": 0, "raison_filtre": "DNS invalide"})
            continue

        # 2. Scraping
        content = fetch_site_content(domain)
        if not content["accessible"]:
            print(f"      ❌ Site inaccessible")
            eliminated.append({**company, "prescore": 0, "raison_filtre": "Site inaccessible"})
            continue

        # 3. Analyse + score
        full_text          = f"{content['title']} {content['description']} {content['keywords']}"
        blacklisted        = detect_blacklist(full_text)
        it_count, it_found = count_it_keywords(full_text)
        prescore           = compute_prescore(True, blacklisted, it_count, company)

        result = {
            **company,
            "prescore"      : prescore,
            "site_title"    : content["title"],
            "site_desc"     : content["description"],
            "it_keywords"   : ", ".join(it_found),
            "raison_filtre" : blacklisted if blacklisted else "",
        }

        if blacklisted:
            print(f"      ❌ Blacklisté ({blacklisted})")
            eliminated.append(result)
        elif prescore < min_prescore:
            print(f"      ⚠️  Pré-score {prescore}/10 trop bas")
            eliminated.append(result)
        else:
            print(f"      ✅ Pré-score {prescore}/10 | IT: {it_found[:3]}")
            to_score.append(result)

        time.sleep(PAUSE)

    return to_score, eliminated
