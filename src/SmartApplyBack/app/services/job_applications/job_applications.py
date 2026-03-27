import os
import re
import json
import base64
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from googleapiclient.discovery import build

from app.services.gmail.gmail import get_credentials
from app.models.job_applications import CandidatureItem, SyncResult

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────
HISTORY_FILE  = os.getenv("JOBS_HISTORY_FILE", "jobs_history.json")
SYNC_META_FILE = os.getenv("SYNC_META_FILE",   "sync_meta.json")
GMAIL_LABEL   = os.getenv("GMAIL_LABEL",        "Candidatures")
MAX_RESULTS   = int(os.getenv("GMAIL_MAX_RESULTS", "200"))


# ══════════════════════════════════════════════════════════════
# PERSISTANCE
# ══════════════════════════════════════════════════════════════

def load_history() -> list[dict]:
    """Charge le fichier jobs_history.json (liste de candidatures)."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(items: list[dict]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2, default=str)


def get_last_sync() -> Optional[datetime]:
    if not os.path.exists(SYNC_META_FILE):
        return None
    with open(SYNC_META_FILE, "r") as f:
        data = json.load(f)
    raw = data.get("last_sync")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def set_last_sync() -> str:
    now = datetime.now(timezone.utc).isoformat()
    with open(SYNC_META_FILE, "w") as f:
        json.dump({"last_sync": now}, f)
    return now


def reset_history() -> None:
    """Supprime l'historique et la date de sync."""
    for path in [HISTORY_FILE, SYNC_META_FILE]:
        if os.path.exists(path):
            os.remove(path)


# ══════════════════════════════════════════════════════════════
# PARSING — traduit ton script Google Sheets en Python
# ══════════════════════════════════════════════════════════════

# ── Emails à ignorer ──────────────────────────────────────────
_IGNORE_PATTERNS = [
    (re.compile(r"alertes?\s+(linkedin|emploi|job)", re.I),       "Alerte emploi"),
    (re.compile(r"pourrait vous convenir", re.I),                  "Recommandation"),
    (re.compile(r"finaliser votre candidature", re.I),             "Relance plateforme"),
    (re.compile(r"terminer votre candidature", re.I),              "Relance plateforme"),
    (re.compile(r"compléter votre candidature", re.I),             "Relance plateforme"),
    (re.compile(r"des offres? (qui )?vous correspondent", re.I),   "Recommandation"),
    (re.compile(r"nouvelles? offres? (d'emploi )?pour vous", re.I),"Recommandation"),
    (re.compile(r"vient de consulter votre (cv|profil)", re.I),    "Vue profil"),
    (re.compile(r"recommandations? d'offres", re.I),               "Recommandation"),
    (re.compile(r"offres? sélectionnées? pour vous", re.I),        "Recommandation"),
    (re.compile(r"sélection d'offres", re.I),                      "Recommandation"),
    (re.compile(r"votre alerte emploi", re.I),                     "Alerte emploi"),
    (re.compile(r"job alert", re.I),                               "Alerte emploi"),
]

_IGNORE_SENDERS = [
    (re.compile(r"jobalerts-noreply@linkedin\.com", re.I), "Alerte LinkedIn"),
    (re.compile(r"jobs-listings@linkedin\.com", re.I),     "Alerte LinkedIn"),
]


def _should_ignore(subject: str, body: str, sender: str) -> Optional[str]:
    """Retourne la raison d'ignorer ou None si le mail est valide."""
    text = (subject + " " + body).lower()
    for pattern, raison in _IGNORE_PATTERNS:
        if pattern.search(text):
            return raison
    for pattern, raison in _IGNORE_SENDERS:
        if pattern.search(sender):
            return raison
    return None


# ── Extraction entreprise ─────────────────────────────────────
def _extract_entreprise(sender: str, subject: str, body: str) -> str:
    nom = ""

    # Hellowork : "l'offre de Acme –"
    m = re.search(r"l'offre de ([^-–\n\r]{1,100}?)\s*[-–]\s*", subject, re.I)
    if m:
        nom = m.group(1).strip()

    # "chez NomEntreprise"
    if not nom:
        m = re.search(r"chez\s+([A-ZÀ-Ÿa-zà-ÿ0-9&.\-]{1,80})(?:\s*[-–(]|$)", subject, re.I)

        if m:
            nom = m.group(1).strip()

    # Nom affiché de l'expéditeur
    if not nom:
        m = re.match(r'"?([^"<]{1,100})"?\s*<', sender)

        if m:
            name = m.group(1).strip()
            if not re.search(r"linkedin|hellowork|indeed|monster|pôle emploi|apec|welcometothejungle", name, re.I):
                nom = name

    # Domaine de l'expéditeur
    if not nom:
        m = re.search(r"@([a-zA-Z0-9-]+)\.", sender)
        if m:
            domain = m.group(1)
            if not re.search(r"gmail|outlook|hotmail|yahoo|linkedin|hellowork|indeed", domain, re.I):
                nom = domain.capitalize()

    nom = re.sub(r"[\"']", "", nom)
    nom = re.sub(r"[^\w\s\-&.àâäéèêëîïôùûüç]", " ", nom, flags=re.I).strip()
    return nom[:50]


# ── Extraction poste ──────────────────────────────────────────
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

    # Fallback : si l'objet contient un titre de poste connu
    if re.search(r"développeur|engineer|dev|analyst|designer|manager|chef|directeur|responsable|consultant", subject, re.I):
        return subject[:60]

    return ""


# ── Extraction ville ──────────────────────────────────────────
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


# ── Détection statut ──────────────────────────────────────────
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


# ── Décodage corps du mail ────────────────────────────────────
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
# SYNC PRINCIPALE
# ══════════════════════════════════════════════════════════════

def sync_candidatures(force_full: bool = False) -> SyncResult:
    """
    Synchronise Gmail → jobs_history.json.
    - Si force_full=True : refetch tous les mails
    - Sinon : seulement les mails depuis la dernière sync
    """
    creds = get_credentials()
    if not creds:
        raise PermissionError("Non authentifié. Lance /gmail/auth")

    service      = build("gmail", "v1", credentials=creds)
    last_sync    = None if force_full else get_last_sync()
    history      = load_history()
    existing_ids = {item["id"] for item in history}

    # ── Récupérer les threads du libellé ─────────────────────
    labels_resp = service.users().labels().list(userId="me").execute()
    label_id    = next(
        (l["id"] for l in labels_resp.get("labels", [])
         if l["name"].lower() == GMAIL_LABEL.lower()),
        None
    )
    if not label_id:
        raise ValueError(f"Libellé '{GMAIL_LABEL}' introuvable dans Gmail")

    query = ""
    if last_sync:
        # after: filtre Gmail en timestamp Unix
        ts    = int(last_sync.timestamp())
        query = f"after:{ts}"

    messages_resp = service.users().messages().list(
        userId="me",
        labelIds=[label_id],
        q=query,
        maxResults=MAX_RESULTS
    ).execute()

    messages = messages_resp.get("messages", [])

    # ── Stats ─────────────────────────────────────────────────
    total     = len(messages)
    nouvelles = 0
    maj       = 0
    ignorees  = 0
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

        # Thread ID pour le lien Gmail
        thread_id  = raw.get("threadId", msg["id"])
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"

        # Date ISO
        received_at = ""
        if date_str:
            try:
                received_at = parsedate_to_datetime(date_str).isoformat()
            except Exception:
                received_at = date_str

        # ── Ignorer ? ────────────────────────────────────────
        raison = _should_ignore(subject, body, sender)
        if raison:
            ignorees += 1
            continue

        # ── Parser ───────────────────────────────────────────
        entreprise = _extract_entreprise(sender, subject, body)
        poste      = _extract_poste(subject, body)
        statut     = _detect_statut(subject, body)
        ville      = _extract_ville(body, subject)

        if not entreprise or not poste:
            sans_poste += 1
            continue

        item = {
            "id":         thread_id,
            "entreprise": entreprise,
            "poste":      poste,
            "statut":     statut,
            "ville":      ville,
            "date":       received_at,
            "expediteur": sender,
            "gmail_link": gmail_link,
        }

        # ── Mise à jour ou ajout ──────────────────────────────
        if thread_id in existing_ids:
            for i, existing in enumerate(history):
                if existing["id"] == thread_id:
                    history[i]["statut"] = statut
                    history[i]["date"]   = received_at
                    if ville:
                        history[i]["ville"] = ville
                    maj += 1
                    break
        else:
            history.append(item)
            existing_ids.add(thread_id)
            nouvelles += 1

    # ── Sauvegarder ───────────────────────────────────────────
    save_history(history)
    sync_time = set_last_sync()

    return SyncResult(
        total_analyses = total,
        nouvelles      = nouvelles,
        mises_a_jour   = maj,
        ignorees       = ignorees,
        sans_poste     = sans_poste,
        derniere_sync  = sync_time,
    )