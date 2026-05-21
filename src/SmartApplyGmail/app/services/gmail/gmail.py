import os
import base64
import re
from datetime import datetime
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests as http_requests

from app.models.gmail import GmailMessage

load_dotenv()

# ── Scopes ────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# ── Config depuis .env ────────────────────────────────────────
CLIENT_ID    = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI")
LABEL         = os.getenv("GMAIL_LABEL", "Candidatures")
MAX_RESULTS   = int(os.getenv("GMAIL_MAX_RESULTS", "50"))


# ── Flow helper (évite la duplication) ───────────────────────

def _make_flow() -> Flow:
    """Instancie un Flow OAuth2 Google réutilisable."""
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )


# ── Auth helpers ──────────────────────────────────────────────

def get_auth_url() -> str:
    import urllib.parse

    params = {
        "client_id":              CLIENT_ID.strip(),
        "redirect_uri":           REDIRECT_URI,
        "response_type":          "code",
        "scope":                  " ".join(SCOPES),
        "access_type":            "offline",
        "include_granted_scopes": "true",
        "prompt":                 "consent",
    }

    query_string = urllib.parse.urlencode(params)
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"


def exchange_code_for_user(code: str) -> tuple[dict, dict]:
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code":          code,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }
    
    token_resp = http_requests.post(token_url, data=data, timeout=10)
    token_resp.raise_for_status()
    token_data = token_resp.json()

    # 2. Récupération des infos utilisateur
    user_info_resp = http_requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )
    user_info_resp.raise_for_status()
    user_info = user_info_resp.json()

    # 3. Formatage des tokens pour la DB
    from datetime import datetime, timedelta
    expiry_date = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))

    tokens = {
        "access_token":  token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"), # Sera présent grâce au prompt=consent
        "expiry":        expiry_date,
        "scopes":        token_data.get("scope", "").split(),
    }

    return user_info, tokens

def refresh_user_token(refresh_token: str) -> dict:
    """
    Rafraîchit l'access_token depuis le refresh_token stocké en DB.
    À appeler quand current_user.token_expiry est dépassée.

    Retourne : { access_token, expiry }
    """
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )
    creds.refresh(Request())

    return {
        "access_token": creds.token,
        "expiry":       creds.expiry,
    }


# ── Extraction ────────────────────────────────────────────────

def _extract_links(text: str) -> list[str]:
    """Extrait tous les liens http(s) d'un texte."""
    return re.findall(r"https?://[^\s\"'<>]+", text)


def _decode_body(payload: dict) -> str:
    """Décode récursivement le corps d'un mail (text/plain)."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def _parse_message(raw: dict, label_name: str) -> GmailMessage:
    """Transforme un message Gmail brut en GmailMessage."""
    headers = {
        h["name"]: h["value"]
        for h in raw.get("payload", {}).get("headers", [])
    }

    subject     = headers.get("Subject")
    sender      = headers.get("From")
    date_str    = headers.get("Date")
    received_at = None

    if date_str:
        try:
            from email.utils import parsedate_to_datetime
            received_at = parsedate_to_datetime(date_str).isoformat()
        except Exception:
            received_at = date_str

    body  = _decode_body(raw.get("payload", {}))
    links = _extract_links(body)

    return GmailMessage(
        id          = raw["id"],
        subject     = subject,
        sender      = sender,
        received_at = received_at,
        body        = body.strip(),
        links       = links,
        label       = label_name,
    )


# ── Fonction principale ───────────────────────────────────────

def fetch_emails_by_label(
    label_name: str,
    access_token: str,
) -> list[GmailMessage]:
    """
    Récupère les mails d'un libellé Gmail pour un utilisateur connecté.

    Plus de token.json — on utilise l'access_token stocké en DB
    et injecté via current_user par la dependency get_current_user.
    """
    creds   = Credentials(token=access_token)
    service = build("gmail", "v1", credentials=creds)

    # 1. Résoudre l'ID du libellé depuis son nom
    labels_response = service.users().labels().list(userId="me").execute()
    label_id = next(
        (
            l["id"]
            for l in labels_response.get("labels", [])
            if l["name"].lower() == label_name.lower()
        ),
        None,
    )
    if not label_id:
        raise ValueError(f"Libellé '{label_name}' introuvable dans Gmail")

    # 2. Lister les messages du libellé
    messages_response = service.users().messages().list(
        userId    = "me",
        labelIds  = [label_id],
        maxResults= MAX_RESULTS,
    ).execute()

    message_ids = messages_response.get("messages", [])
    results     = []

    # 3. Récupérer chaque message en détail
    for msg in message_ids:
        raw = service.users().messages().get(
            userId = "me",
            id     = msg["id"],
            format = "full",
        ).execute()
        results.append(_parse_message(raw, label_name))

    return results


# ── Draft creation ────────────────────────────────────────────

def create_gmail_draft(
    access_token: str,
    subject: str,
    body: str,
    to: str = "",
) -> dict:
    import base64
    from email.mime.text import MIMEText

    creds   = Credentials(token=access_token)
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body, "plain", "utf-8")
    message["subject"] = subject
    if to:
        message["to"] = to

    raw   = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft = service.users().drafts().create(
        userId = "me",
        body   = {"message": {"raw": raw}},
    ).execute()

    draft_id   = draft["id"]
    message_id = draft.get("message", {}).get("id", "")
    draft_url  = f"https://mail.google.com/mail/#drafts/{message_id}"

    return {"draft_id": draft_id, "draft_url": draft_url}