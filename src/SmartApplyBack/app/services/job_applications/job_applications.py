import re
import base64
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from googleapiclient.discovery import build

from app.models.job_applications import CandidatureItem, SyncResult

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────
GMAIL_LABEL = "Candidatures"
MAX_RESULTS = 1000


# ══════════════════════════════════════════════════════════════
# PARSING
# ══════════════════════════════════════════════════════════════

_IGNORE_PATTERNS = [
    (re.compile(r"alertes?\s+(linkedin|emploi|job)", re.I),        "Alerte emploi"),
    (re.compile(r"pourrait vous convenir", re.I),                   "Recommandation"),
    (re.compile(r"finaliser votre candidature", re.I),              "Relance plateforme"),
    (re.compile(r"terminer votre candidature", re.I),               "Relance plateforme"),
    (re.compile(r"compléter votre candidature", re.I),              "Relance plateforme"),
    (re.compile(r"des offres? (qui )?vous correspondent", re.I),    "Recommandation"),
    (re.compile(r"nouvelles? offres? (d'emploi )?pour vous", re.I), "Recommandation"),
    (re.compile(r"vient de consulter votre (cv|profil)", re.I),     "Vue profil"),
    (re.compile(r"recommandations? d'offres", re.I),                "Recommandation"),
    (re.compile(r"offres? sélectionnées? pour vous", re.I),         "Recommandation"),
    (re.compile(r"sélection d'offres", re.I),                       "Recommandation"),
    (re.compile(r"votre alerte emploi", re.I),                      "Alerte emploi"),
    (re.compile(r"job alert", re.I),                                "Alerte emploi"),
]

_IGNORE_SENDERS = [
    (re.compile(r"jobalerts-noreply@linkedin\.com", re.I), "Alerte LinkedIn"),
    (re.compile(r"jobs-listings@linkedin\.com", re.I),     "Alerte LinkedIn"),
]


def _should_ignore(subject: str, body: str, sender: str) -> Optional[str]:
    text = (subject + " " + body).lower()
    for pattern, raison in _IGNORE_PATTERNS:
        if pattern.search(text):
            return raison
    for pattern, raison in _IGNORE_SENDERS:
        if pattern.search(sender):
            return raison
    return None


def _extract_entreprise(sender: str, subject: str, body: str) -> str:
    nom = ""
    m = re.search(r"l'offre de ([^-–\n\r]{1,100}?)\s*[-–]\s*", subject, re.I)
    if m:
        nom = m.group(1).strip()
    if not nom:
        m = re.search(r"chez\s+([A-ZÀ-Ÿa-zà-ÿ0-9&.\-]{1,80})(?:\s*[-–(]|$)", subject, re.I)
        if m:
            nom = m.group(1).strip()
    if not nom:
        m = re.match(r'"?([^"<]{1,100})"?\s*<', sender)
        if m:
            name = m.group(1).strip()
            if not re.search(r"linkedin|hellowork|indeed|monster|pôle emploi|apec|welcometothejungle", name, re.I):
                nom = name
    if not nom:
        m = re.search(r"@([a-zA-Z0-9-]+)\.", sender)
        if m:
            domain = m.group(1)
            if not re.search(r"gmail|outlook|hotmail|yahoo|linkedin|hellowork|indeed", domain, re.I):
                nom = domain.capitalize()
    nom = re.sub(r"[\"']", "", nom)
    nom = re.sub(r"[^\w\s\-&.àâäéèêëîïôùûüç]", " ", nom, flags=re.I).strip()
    return nom[:50]


def _extract_poste(subject: str, body: str) -> str:
    text = subject + " " + body
    patterns = [
        re.compile(r"(?:poste|offre)\s*[:\-–]\s*([^\n\r,|]{5,60})", re.I),
        re.compile(r"candidature\s+(?:au?|pour le?|pour la?|au poste de?)\s+([^\n\r,|]{5,60})", re.I),
        re.compile(r"(?:pour le poste de?|au poste de?)\s+([^\n\r,|]{5,60})", re.I),
        re.compile(r"l'offre de [^-–\n\r]{0,100}?\s*[-–]\s*([^\n\r(]{5,60})", re.I),
        re.compile(r"poste de\s+([^\n\r,|]{5,60}?)(?:\s+chez|\s+[-–]|$)", re.I),
    ]
    for p in patterns:
        m = p.search(text)
        if m:
            result = re.sub(r"\s+H\/F$", "", m.group(1).strip(), flags=re.I)[:60]
            if not re.match(r"^(emploi|job|travail|poste|offre)$", result, re.I):
                return result
    if re.search(r"développeur|engineer|dev|analyst|designer|manager|chef|directeur|responsable|consultant", subject, re.I):
        return subject[:60]
    return ""


_VILLES_FR = (
    r"Paris|Lyon|Marseille|Toulouse|Bordeaux|Nantes|Lille|Strasbourg|Montpellier|Nice|"
    r"Rennes|Grenoble|Rouen|Toulon|Saint-Étienne|Dijon|Angers|Nîmes|Le Mans|"
    r"Aix-en-Provence|Brest|Limoges|Tours|Amiens|Perpignan|Metz|Besançon|Orléans|"
    r"Mulhouse|Caen|Nancy|Boulogne-Billancourt|Nanterre|Levallois-Perret|Neuilly-sur-Seine|"
    r"La Rochelle|Clermont-Ferrand|Annecy|Montauban"
)


def _extract_ville(body: str, subject: str) -> str:
    text = body + " " + subject
    patterns = [
        re.compile(rf"\b({_VILLES_FR})\b", re.I),
        re.compile(r"(?:lieu|localisation|ville|site|basé[e]? à|poste basé|localis[ée] à)[\s:\-–]{0,3}([A-ZÀ-Ÿ][a-zà-ÿ\-]{1,30}(?:\s[A-ZÀ-Ÿ][a-zà-ÿ\-]{1,30})?)", re.I),
        re.compile(r"\b([A-ZÀ-Ÿ][a-zà-ÿ\-]+)\s*\((?:0[1-9]|[1-8]\d|9[0-5])\)"),
    ]
    for p in patterns:
        m = p.search(text)
        if m:
            ville = (m.group(1) if m.lastindex else m.group(0)).strip()[:40]
            if not re.match(r"^(emploi|job|travail|poste|offre|télétravail|remote|hybrid)$", ville, re.I):
                return ville
    return ""


def _detect_statut(subject: str, body: str) -> str:
    text = (subject + " " + body).lower()
    if re.search(r"refus|malheureusement|ne correspond pas|ne retien|n'avons pas retenu|nous n'avons pas|candidature.*déclin|ne donnera pas suite", text):
        return "Refusé"
    if re.search(r"entretien|interview|rendez-vous|meeting|rencontre|nous souhaitons vous rencontrer", text):
        return "Entretien"
    if re.search(r"félicitation|bienvenue|nous sommes heureux de vous proposer", text):
        return "Offre reçue"
    if re.search(r"décision|en cours|traitement|étude|examen de votre candidature|bien reçu|prise en compte", text):
        return "Décision requise"
    return "En attente"


def _decode_body(payload: dict) -> str:
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data", "")
    if mime == "text/plain" and data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result
    return ""


# ══════════════════════════════════════════════════════════════
# SYNC PRINCIPALE — reçoit access_token + repo au lieu de fichiers
# ══════════════════════════════════════════════════════════════

def sync_candidatures(
    access_token: str,
    user_id: str,
    repo, 
    force_full: bool = False,
) -> SyncResult:
    """
    Synchronise Gmail → MongoDB.
    Plus de fichiers JSON — tout passe par le repo.
    access_token et user_id viennent du current_user injecté par le router.
    """
    from google.oauth2.credentials import Credentials
    creds = Credentials(token=access_token)
    service = build("gmail", "v1", credentials=creds)

    # On utilise le repo au lieu des fichiers
    existing = repo.find_by_user(user_id)
    existing_ids = {item["thread_id"] for item in existing}
    last_sync = None if force_full else repo.get_last_sync(user_id)

    # Résoudre l'ID du libellé
    labels_resp = service.users().labels().list(userId="me").execute()
    label_id    = next(
        (l["id"] for l in labels_resp.get("labels", [])
         if l["name"].lower() == GMAIL_LABEL.lower()),
        None,
    )
    if not label_id:
        raise ValueError(f"Libellé '{GMAIL_LABEL}' introuvable dans Gmail")

    query = ""
    if last_sync:
        query = f"after:{int(last_sync.timestamp())}"

    messages_resp = service.users().messages().list(
        userId    = "me",
        labelIds  = [label_id],
        q         = query,
        maxResults= MAX_RESULTS,
    ).execute()

    messages   = messages_resp.get("messages", [])
    total      = len(messages)
    nouvelles  = 0
    maj        = 0
    ignorees   = 0
    sans_poste = 0

    for msg in messages:
        raw = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()

        headers  = {h["name"]: h["value"] for h in raw.get("payload", {}).get("headers", [])}
        subject  = headers.get("Subject", "")
        sender   = headers.get("From", "")
        date_str = headers.get("Date", "")
        body     = _decode_body(raw.get("payload", {}))

        thread_id  = raw.get("threadId", msg["id"])
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"

        received_at = ""
        if date_str:
            try:
                received_at = parsedate_to_datetime(date_str).isoformat()
            except Exception:
                received_at = date_str

        raison = _should_ignore(subject, body, sender)
        if raison:
            ignorees += 1
            continue

        entreprise = _extract_entreprise(sender, subject, body)
        poste      = _extract_poste(subject, body)
        statut     = _detect_statut(subject, body)
        ville      = _extract_ville(body, subject)

        if not entreprise or not poste:
            sans_poste += 1
            continue

        item = {
            "user_id":    user_id,       # ← clé multi-user
            "thread_id":  thread_id,
            "entreprise": entreprise,
            "poste":      poste,
            "statut":     statut,
            "ville":      ville,
            "date":       received_at,
            "expediteur": sender,
            "gmail_link": gmail_link,
        }

        if thread_id in existing_ids:
            repo.update_statut(user_id, thread_id, statut, received_at, ville)
            maj += 1
        else:
            repo.save(item)
            existing_ids.add(thread_id)
            nouvelles += 1

    sync_time = repo.set_last_sync(user_id)

    return SyncResult(
        total_analyses=total,
        nouvelles=nouvelles,
        mises_a_jour=maj,
        ignorees=ignorees,
        sans_poste=sans_poste,
        derniere_sync=sync_time,
    )


def load_history(user_id: str, repo) -> list:
    """Remplace l'ancien load_history() en lisant MongoDB via le repo."""
    return repo.find_by_user(user_id)

def get_last_sync(user_id: str, repo):
    """Remplace l'ancien get_last_sync() via MongoDB."""
    return repo.get_last_sync(user_id)

def reset_history(user_id: str, repo):
    """Remplace l'ancien reset_history() via MongoDB."""
    return repo.delete_all_by_user(user_id)