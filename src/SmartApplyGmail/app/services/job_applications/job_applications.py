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

    # Récupération de l'existant (on s'assure que c'est une liste de dicts)
    existing = repo.find_by_user(user_id) or []
    last_sync = None if force_full else repo.get_last_sync(user_id)

    # Résolution du label Gmail
    labels_resp = service.users().labels().list(userId="me").execute()
    label_id = next(
        (l["id"] for l in labels_resp.get("labels", [])
         if l["name"].lower() == GMAIL_LABEL.lower()),
        None,
    )
    
    if not label_id:
        raise ValueError(f"Libellé '{GMAIL_LABEL}' introuvable dans Gmail")

    # Sécurisation de la query de date
    query = ""
    if last_sync and hasattr(last_sync, 'timestamp'):
        query = f"after:{int(last_sync.timestamp())}"

    messages_resp = service.users().messages().list(
        userId="me",
        labelIds=[label_id],
        q=query,
        maxResults=MAX_RESULTS,
    ).execute()

    messages   = messages_resp.get("messages", [])
    total      = len(messages)
    nouvelles  = 0
    maj        = 0
    ignorees   = 0
    sans_poste = 0

    for msg in messages:
        try:
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
                except:
                    received_at = date_str

            # ── 1. Filtre Spam/Alertes ──
            raison = should_ignore(subject, body, sender)
            if raison:
                ignorees += 1
                logger.info(f"[IGNORÉ] {subject[:40]} | Raison: {raison}")
                continue

            # ── 2. Extraction des données ──
            entreprise = extract_entreprise(sender, subject, body)
            poste      = extract_poste(subject, body, sender)
            statut     = detect_statut(subject, body, sender)
            ville      = extract_ville(body, subject, sender)

            # ── 3. Logique de Doublon (Entreprise + Poste) ──
            # On utilise .get() partout pour éviter les KeyError qui causent des 500
            match_existant = next(
                (item for item in existing 
                 if str(item.get("entreprise", "")).lower() == entreprise.lower() 
                 and str(item.get("poste", "")).lower() == poste.lower()), 
                None
            )

            if match_existant:
                ancien_statut = match_existant.get("statut", "En attente")
                if should_upgrade_statut(ancien_statut, statut):
                    # Mise à jour du statut en base
                    repo.update_statut(user_id, match_existant.get("thread_id"), statut, received_at, ville)
                    match_existant["statut"] = statut
                    maj += 1
                    logger.info(f"[MAJ] {entreprise} : {ancien_statut} -> {statut}")
            else:
                # Nouvelle candidature
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
                existing.append(item)
                nouvelles += 1
                logger.info(f"[NOUVEAU] {entreprise} - {poste}")

        except Exception as e:
            logger.error(f"Erreur lors du traitement d'un message Gmail: {str(e)}")
            continue

    # Mise à jour de la date de dernière sync
    sync_time = repo.set_last_sync(user_id)
    clear_cache()

    return SyncResult(
        total_analyses=total,
        nouvelles=nouvelles,
        mises_a_jour=maj,
        ignorees=ignorees,
        sans_poste=sans_poste,
        derniere_sync=sync_time if isinstance(sync_time, str) else str(sync_time),
    )

def load_history(user_id: str, repo) -> list:
    return repo.find_by_user(user_id)

def get_last_sync(user_id: str, repo):
    return repo.get_last_sync(user_id)

def reset_history(user_id: str, repo):
    return repo.delete_all_by_user(user_id)