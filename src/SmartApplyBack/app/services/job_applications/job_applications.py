"""
job_applications.py
-------------------
Synchronisation Gmail → MongoDB.
Utilise gmail_ollama_parser pour le parsing des emails.
"""

import base64
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build

from app.models.job_applications import CandidatureItem, SyncResult
from app.services.job_applications.gmail_ollama_parser import (
    should_ignore,
    extract_entreprise,
    extract_poste,
    extract_ville,
    detect_statut,
    should_upgrade_statut,
    clear_cache,
)

logger = logging.getLogger(__name__)

GMAIL_LABEL = "Candidatures"
MAX_RESULTS = 1000


# ══════════════════════════════════════════════════════════════
# DÉCODAGE BODY
# ══════════════════════════════════════════════════════════════

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

def sync_candidatures(
    access_token: str,
    user_id: str,
    repo,
    force_full: bool = False,
) -> SyncResult:
    from google.oauth2.credentials import Credentials

    creds   = Credentials(token=access_token)
    service = build("gmail", "v1", credentials=creds)

    existing     = repo.find_by_user(user_id)
    existing_map = {item["thread_id"]: item for item in existing}   # ← dict pour accès rapide
    last_sync    = None if force_full else repo.get_last_sync(user_id)

    # Résolution du label Gmail
    labels_resp = service.users().labels().list(userId="me").execute()
    label_id    = next(
        (l["id"] for l in labels_resp.get("labels", [])
         if l["name"].lower() == GMAIL_LABEL.lower()),
        None,
    )
    if not label_id:
        raise ValueError(f"Libellé '{GMAIL_LABEL}' introuvable dans Gmail")

    query = f"after:{int(last_sync.timestamp())}" if last_sync else ""

    messages_resp = service.users().messages().list(
        userId    ="me",
        labelIds  =[label_id],
        q         =query,
        maxResults=MAX_RESULTS,
    ).execute()

    messages   = messages_resp.get("messages", [])
    total      = len(messages)
    nouvelles  = 0
    maj        = 0
    ignorees   = 0
    sans_poste = 0  # gardé pour compatibilité SyncResult mais ne jette plus d'emails

    for msg in messages:
        raw = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()

        headers     = {h["name"]: h["value"] for h in raw.get("payload", {}).get("headers", [])}
        subject     = headers.get("Subject", "")
        sender      = headers.get("From", "")
        date_str    = headers.get("Date", "")
        body        = _decode_body(raw.get("payload", {}))
        thread_id   = raw.get("threadId", msg["id"])
        gmail_link  = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"

        received_at = ""
        if date_str:
            try:
                received_at = parsedate_to_datetime(date_str).isoformat()
            except Exception:
                received_at = date_str

        # ── Filtre spam/alertes ──
        raison = should_ignore(subject, body, sender)
        if raison:
            ignorees += 1
            logger.debug("[IGNORÉ] %s | raison: %s", subject[:60], raison)
            continue

        # ── Extraction ──
        entreprise = extract_entreprise(sender, subject, body)
        poste      = extract_poste(subject, body, sender)
        statut     = detect_statut(subject, body, sender)
        ville      = extract_ville(body, subject, sender)

        # ── Thread déjà connu → mise à jour intelligente du statut ──
        if thread_id in existing_map:
            ancien_statut = existing_map[thread_id].get("statut", "En attente")

            # On met à jour uniquement si le nouveau statut est plus important
            if should_upgrade_statut(ancien_statut, statut):
                repo.update_statut(user_id, thread_id, statut, received_at, ville)
                existing_map[thread_id]["statut"] = statut
                logger.info(
                    "[MAJ] %s | %s → %s", subject[:50], ancien_statut, statut
                )
                maj += 1
            else:
                logger.debug(
                    "[SKIP MAJ] %s | statut conservé: %s (nouveau: %s)",
                    subject[:50], ancien_statut, statut,
                )
        else:
            # ── Nouveau thread ──
            item = {
                "user_id":    user_id,
                "thread_id":  thread_id,
                "entreprise": entreprise,
                "poste":      poste,
                "statut":     statut,
                "ville":      ville,
                "date":       received_at,
                "expediteur": sender,
                "gmail_link": gmail_link,
            }
            repo.save(item)
            existing_map[thread_id] = item
            nouvelles += 1
            logger.info("[NOUVEAU] %s | %s @ %s | %s", subject[:50], poste, entreprise, statut)

    sync_time = repo.set_last_sync(user_id)
    clear_cache()

    return SyncResult(
        total_analyses=total,
        nouvelles=nouvelles,
        mises_a_jour=maj,
        ignorees=ignorees,
        sans_poste=sans_poste,
        derniere_sync=sync_time,
    )


def load_history(user_id: str, repo) -> list:
    return repo.find_by_user(user_id)

def get_last_sync(user_id: str, repo):
    return repo.get_last_sync(user_id)

def reset_history(user_id: str, repo):
    return repo.delete_all_by_user(user_id)