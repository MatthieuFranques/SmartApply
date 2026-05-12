"""
gmail_ollama_parser.py
----------------------
Parser d'emails de recrutement via Ollama.

Philosophie :
  - On pose à Ollama UNE seule question simple à la fois, pas un JSON complexe.
  - La logique métier (doublon, priorité des statuts) reste en Python.
  - Si Ollama échoue ou est trop lent → fallback regex robuste FR+EN.

Config dans .env (voir .env.example).
"""

import json
import logging
import os
import re
from typing import Optional

import ollama
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════

class OllamaConfig:
    model:             str       = os.getenv("OLLAMA_MODEL",              "mistral")
    host:              str       = os.getenv("OLLAMA_HOST",               "http://localhost:11434")
    temperature:       float     = float(os.getenv("OLLAMA_TEMPERATURE",  "0.0"))
    max_tokens:        int       = int(os.getenv("OLLAMA_MAX_TOKENS",     "256"))
    timeout:           int       = int(os.getenv("OLLAMA_TIMEOUT",        "30"))
    body_max_chars:    int       = int(os.getenv("OLLAMA_BODY_MAX_CHARS", "3000"))
    fallback_enabled:  bool      = os.getenv("OLLAMA_FALLBACK_ENABLED",  "true").lower() == "true"
    langs:             list[str] = [
        l.strip() for l in os.getenv("OLLAMA_EMAIL_LANGS", "fr,en").split(",") if l.strip()
    ]

cfg = OllamaConfig()


# ══════════════════════════════════════════════════════════════
# HELPERS OLLAMA — appels simples, une question à la fois
# ══════════════════════════════════════════════════════════════

def _ask(prompt: str) -> str:
    """Appelle Ollama et retourne le texte brut de la réponse."""
    client = ollama.Client(host=cfg.host)
    resp   = client.chat(
        model=cfg.model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
    )
    return resp["message"]["content"].strip().lower()


def _ask_json(prompt: str) -> dict:
    """Appelle Ollama et tente de parser la réponse en JSON."""
    client = ollama.Client(host=cfg.host)
    resp   = client.chat(
        model=cfg.model,
        messages=[
            {
                "role": "system",
                "content": "Reply ONLY with valid JSON. No markdown, no backticks, no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
    )
    raw = resp["message"]["content"].strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ══════════════════════════════════════════════════════════════
# REGEX ROBUSTES FR + EN — utilisées en fallback ET pour pré-filtrer
# ══════════════════════════════════════════════════════════════

# — Emails à ignorer —
_IGNORE_SENDERS = [
    re.compile(r"jobalerts-noreply@linkedin\.com", re.I),
    re.compile(r"jobs-listings@linkedin\.com", re.I),
    re.compile(r"jobalerts@linkedin\.com", re.I),
    re.compile(r"noreply@indeed\.com", re.I),
    re.compile(r"alert@glassdoor\.com", re.I),
    re.compile(r"noreply@welcometothejungle\.com", re.I),
]

_IGNORE_RE = re.compile(
    r"alertes?\s+(linkedin|emploi|job)|job alert|"
    r"pourrait vous convenir|jobs? you might like|jobs? recommended for you|"
    r"finaliser votre candidature|complete your application|finish your application|"
    r"terminer votre candidature|compléter votre candidature|"
    r"des offres? (qui )?vous correspondent|new jobs? for you|top jobs? this week|"
    r"nouvelles? offres? (d'emploi )?pour vous|based on your profile|"
    r"vient de consulter votre (cv|profil)|viewed your profile|"
    r"recommandations? d'offres|offres? sélectionnées? pour vous|"
    r"sélection d'offres|votre alerte emploi|people also viewed",
    re.I,
)

# — Statuts —
_REFUS_RE = re.compile(
    r"refus|malheureusement|ne correspond pas|ne retien|n'avons pas retenu|"
    r"nous n'avons pas retenu|candidature.*déclin|ne donnera pas suite|"
    r"unfortunately|we regret|not selected|not moving forward|"
    r"decided not to proceed|we will not be moving|after careful consideration|"
    r"we won't be|we are not|position has been filled|no longer considering",
    re.I,
)
_ENTRETIEN_RE = re.compile(
    r"entretien|interview|rendez-vous|meeting|rencontre|"
    r"nous souhaitons vous rencontrer|schedule a call|phone screen|"
    r"video call|we.d like to speak|would like to invite|"
    r"disponibilités|availability|slots|book a time",
    re.I,
)
_OFFRE_RE = re.compile(
    r"félicitation|bienvenue dans|nous sommes heureux de vous proposer|"
    r"congratulations|pleased to offer|offer of employment|"
    r"job offer|lettre d'offre|nous avons le plaisir de vous offrir",
    re.I,
)
_DECISION_RE = re.compile(
    r"bien reçu|prise en compte|examen de votre candidature|"
    r"under review|received your application|application received|"
    r"we will review|currently reviewing|will be in touch|"
    r"en cours d'examen|étude de votre|traitement de votre",
    re.I,
)

# Priorité des statuts : si un email a des signaux de plusieurs types,
# on prend le plus important (Offre > Entretien > Refusé > Décision > En attente)
_STATUT_PRIORITY = ["Offre reçue", "Entretien", "Refusé", "Décision requise", "En attente"]

def _detect_statut_regex(text: str) -> str:
    if _OFFRE_RE.search(text):     return "Offre reçue"
    if _ENTRETIEN_RE.search(text): return "Entretien"
    if _REFUS_RE.search(text):     return "Refusé"
    if _DECISION_RE.search(text):  return "Décision requise"
    return "En attente"

def _is_ignored_regex(subject: str, body: str, sender: str) -> Optional[str]:
    for pattern in _IGNORE_SENDERS:
        if pattern.search(sender):
            return "Expéditeur automatique"
    text = subject + " " + body[:500]
    if _IGNORE_RE.search(text):
        return "Email non-candidature"
    return None


# ══════════════════════════════════════════════════════════════
# STRATÉGIE : regex d'abord, Ollama uniquement si ambigu
# ══════════════════════════════════════════════════════════════
#
# Raisonnement :
#   Les regex sont très fiables pour détecter les spams/alertes et les
#   statuts évidents. Ollama n'est appelé QUE pour les cas ambigus
#   (ni refus clair, ni entretien clair, ni spam clair) — là où il apporte
#   vraiment de la valeur. Ça évite de gaspiller du temps sur les cas simples
#   ET ça réduit les erreurs du modèle sur des emails évidents.

def _statut_is_ambiguous(statut_regex: str, text: str) -> bool:
    """
    Retourne True si le résultat regex est peu fiable et mérite confirmation Ollama.
    Un statut 'En attente' sur un email assez long = ambigu (peut-être un refus poli).
    """
    if statut_regex != "En attente":
        return False
    # Court email sans signal clair = probablement vraiment "En attente"
    if len(text) < 200:
        return False
    # Email long sans aucun signal = potentiellement un refus poli ou une offre
    return True


def parse_email(sender: str, subject: str, body: str) -> dict:
    """
    Parse un email de recrutement.
    Retourne : ignorer (bool), raison_ignore, entreprise, poste, ville, statut.
    
    Stratégie :
      1. Regex rapide pour les cas évidents (spam, alertes, refus nets, entretiens)
      2. Ollama uniquement pour les cas ambigus et pour extraire entreprise/poste
      3. Fallback regex complet si Ollama échoue
    """
    text_full = subject + "\n" + body
    text_low  = text_full.lower()

    # ── Étape 1 : filtre spam/alertes (regex, très fiable) ──
    raison_ignore = _is_ignored_regex(subject, body, sender)
    if raison_ignore:
        return {
            "ignorer": True, "raison_ignore": raison_ignore,
            "entreprise": "", "poste": "", "ville": "", "statut": "En attente",
        }

    # ── Étape 2 : détection statut par regex ──
    statut = _detect_statut_regex(text_low)

    # ── Étape 3 : Ollama pour extraire entreprise/poste ET confirmer statut ambigu ──
    entreprise, poste, ville = "", "", ""
    ollama_ok = False

    try:
        body_snippet = body[:cfg.body_max_chars]

        # Question unique et simple pour Ollama
        prompt = f"""This is a recruitment email. Extract information and return JSON.

Sender: {sender[:200]}
Subject: {subject[:300]}
Body:
{body_snippet}

Return this JSON:
{{
  "is_job_application": true or false,
  "company": "company name or empty string",
  "job_title": "job title or empty string",
  "city": "city name or empty string",
  "status": one of: "rejected" / "interview" / "offer" / "pending" / "waiting"
}}

Rules:
- is_job_application: false if this is a job alert, newsletter, recommendation, or automated platform email
- company: the hiring company name (NOT LinkedIn, Indeed, HelloWork etc.)
- job_title: the actual position title
- city: city of the job if mentioned
- status:
    "rejected"  = refusal email
    "interview" = invitation to interview or call
    "offer"     = job offer / hiring proposal
    "pending"   = application acknowledged, under review
    "waiting"   = no clear status signal"""

        result = _ask_json(prompt)

        # Mapping statut anglais → statut FR de l'appli
        _status_map = {
            "rejected":  "Refusé",
            "interview": "Entretien",
            "offer":     "Offre reçue",
            "pending":   "Décision requise",
            "waiting":   "En attente",
        }

        # Si Ollama dit que ce n'est pas une candidature
        if not result.get("is_job_application", True):
            return {
                "ignorer": True, "raison_ignore": "Non-candidature (IA)",
                "entreprise": "", "poste": "", "ville": "", "statut": "En attente",
            }

        entreprise = str(result.get("company", "")).strip()[:50]
        poste      = str(result.get("job_title", "")).strip()[:60]
        ville      = str(result.get("city", "")).strip()[:40]

        # Ollama a la priorité sur le statut si le résultat regex était ambigu
        ollama_statut = _status_map.get(result.get("status", ""), None)
        if ollama_statut and _statut_is_ambiguous(statut, text_low):
            statut = ollama_statut
        elif ollama_statut and statut == "En attente":
            # Ollama peut upgrader un "En attente" regex vers quelque chose de plus précis
            statut = ollama_statut

        ollama_ok = True

    except Exception as e:
        logger.warning("[Ollama] Échec pour '%s': %s", subject[:60], e)

    # ── Étape 4 : si Ollama a échoué, tentative d'extraction regex basique ──
    if not ollama_ok:
        if cfg.fallback_enabled:
            logger.info("[Ollama] Fallback regex pour '%s'", subject[:60])
            # Extraction entreprise depuis expéditeur
            m = re.match(r'"?([^"<]{2,60})"?\s*<', sender)
            if m:
                name = m.group(1).strip()
                if not re.search(r"linkedin|hellowork|indeed|monster|apec|welcometothejungle|noreply|no-reply", name, re.I):
                    entreprise = name[:50]
            if not entreprise:
                m = re.search(r"@([a-zA-Z0-9-]+)\.", sender)
                if m:
                    domain = m.group(1)
                    if not re.search(r"gmail|outlook|hotmail|yahoo|linkedin|hellowork|indeed", domain, re.I):
                        entreprise = domain.capitalize()
            # Extraction poste depuis sujet
            for pat in [
                re.compile(r"(?:poste|offre|position)\s*[:\-–]\s*([^\n\r,|]{5,60})", re.I),
                re.compile(r"candidature\s+(?:au?|pour le?|pour la?)\s+([^\n\r,|]{5,60})", re.I),
                re.compile(r"(?:developer|engineer|analyst|designer|manager|consultant|développeur|ingénieur|responsable|chef)\s[^\n\r,|]{0,40}", re.I),
            ]:
                m = pat.search(subject)
                if m:
                    poste = m.group(0).strip()[:60]
                    break

    # ── Étape 5 : placeholder si poste toujours vide (on ne jette plus l'email) ──
    if not poste:
        # On essaie d'extraire depuis le sujet en dernier recours
        poste = subject.strip()[:60] if subject.strip() else "Poste non précisé"

    if not entreprise:
        entreprise = "Entreprise inconnue"

    return {
        "ignorer":      False,
        "raison_ignore": "",
        "entreprise":   entreprise,
        "poste":        poste,
        "ville":        ville,
        "statut":       statut,
    }


# ══════════════════════════════════════════════════════════════
# LOGIQUE DE MISE À JOUR DU STATUT — priorité aux statuts importants
# ══════════════════════════════════════════════════════════════

def should_upgrade_statut(ancien: str, nouveau: str) -> bool:
    """
    Retourne True si le nouveau statut est plus important que l'ancien.
    On ne rétrograde jamais un statut important (ex: Entretien → En attente).
    Ordre : Offre reçue > Entretien > Refusé > Décision requise > En attente
    """
    try:
        return _STATUT_PRIORITY.index(nouveau) < _STATUT_PRIORITY.index(ancien)
    except ValueError:
        return False


# ══════════════════════════════════════════════════════════════
# CACHE — une seule passe par email dans un même sync
# ══════════════════════════════════════════════════════════════

_cache: dict[str, dict] = {}


def _get_parsed(sender: str, subject: str, body: str) -> dict:
    key = f"{sender[:50]}|{subject[:80]}"
    if key not in _cache:
        _cache[key] = parse_email(sender, subject, body)
    return _cache[key]


# ══════════════════════════════════════════════════════════════
# API PUBLIQUE
# ══════════════════════════════════════════════════════════════

def should_ignore(subject: str, body: str, sender: str) -> Optional[str]:
    parsed = _get_parsed(sender, subject, body)
    if parsed.get("ignorer"):
        return parsed.get("raison_ignore") or "Ignoré"
    return None

def extract_entreprise(sender: str, subject: str, body: str) -> str:
    return _get_parsed(sender, subject, body).get("entreprise", "Entreprise inconnue")

def extract_poste(subject: str, body: str, sender: str = "") -> str:
    return _get_parsed(sender, subject, body).get("poste", "Poste non précisé")

def extract_ville(body: str, subject: str, sender: str = "") -> str:
    return _get_parsed(sender, subject, body).get("ville", "")

def detect_statut(subject: str, body: str, sender: str = "") -> str:
    return _get_parsed(sender, subject, body).get("statut", "En attente")

def clear_cache() -> None:
    _cache.clear()