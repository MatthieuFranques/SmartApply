import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import requests
from scraping_config import HUNTER_API_KEY


def get_email_from_domain(domain: str) -> dict:
    """
    Récupère l'email de contact d'une entreprise depuis son domaine.
    Priorité aux emails génériques (contact@, info@),
    fallback sur email personnel si aucun générique trouvé.
    Consomme 1 quota Hunter par appel.

    Paramètres :
        domain : nom de domaine, ex. "monentreprise.fr"

    Retourne :
        Dict avec les clés : email, organisation.
    """
    url = "https://api.hunter.io/v2/domain-search"

    try:
        email, organisation = _fetch_generic_email(url, domain)

        if not email:
            email, organisation = _fetch_personal_email(url, domain)

        return {"email": email, "organisation": organisation}

    except Exception as e:
        print(f"  [Domain Search] Erreur {domain} : {e}")
        return {"email": "", "organisation": ""}


def _fetch_generic_email(url: str, domain: str) -> tuple[str, str]:
    """Tente de récupérer un email générique (contact@, info@…)."""
    response = requests.get(url, params={
        "domain" : domain,
        "api_key": HUNTER_API_KEY,
        "limit"  : 3,
        "type"   : "generic",
    }, timeout=10)
    response.raise_for_status()

    data   = response.json().get("data", {})
    emails = data.get("emails", [])

    if emails:
        return emails[0].get("value", ""), data.get("organization", "")

    return "", ""


def _fetch_personal_email(url: str, domain: str) -> tuple[str, str]:
    """Fallback : récupère un email personnel si aucun générique n'existe."""
    response = requests.get(url, params={
        "domain" : domain,
        "api_key": HUNTER_API_KEY,
        "limit"  : 3,
        "type"   : "personal",
    }, timeout=10)
    response.raise_for_status()

    data   = response.json().get("data", {})
    emails = data.get("emails", [])

    email = emails[0].get("value", "") if emails else ""
    return email, data.get("organization", "")