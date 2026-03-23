import os
import base64
import re
from email import message_from_bytes
from datetime import datetime
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv

from app.models.gmail import GmailMessage

load_dotenv()

# ── Scopes ────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# ── Config depuis .env ────────────────────────────────────────
CLIENT_ID       = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET   = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI    = os.getenv("GOOGLE_REDIRECT_URI")
TOKEN_PATH      = os.getenv("GMAIL_TOKEN_PATH", "token.json")
LABEL           = os.getenv("GMAIL_LABEL", "Candidatures")
MAX_RESULTS     = int(os.getenv("GMAIL_MAX_RESULTS", "50"))


# ── Auth helpers ─────────────────────────────────────────────

def get_auth_url() -> str:
    """Génère l'URL d'autorisation Google (1ère connexion)."""
    flow = Flow.from_client_config(
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
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def save_token_from_code(code: str) -> None:
    """Échange le code OAuth contre un token et le sauvegarde."""
    flow = Flow.from_client_config(
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
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())


def get_credentials() -> Optional[Credentials]:
    """Charge et rafraîchit les credentials depuis token.json."""
    if not os.path.exists(TOKEN_PATH):
        return None

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds if creds and creds.valid else None


# ── Extraction ───────────────────────────────────────────────

def _extract_links(text: str) -> list[str]:
    """Extrait tous les liens http(s) d'un texte."""
    return re.findall(r"https?://[^\s\"'<>]+", text)


def _decode_body(payload: dict) -> str:
    """Décode récursivement le corps d'un mail (text/plain)."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

    # Multipart : on cherche text/plain en priorité
    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def _parse_message(raw: dict, label_name: str) -> GmailMessage:
    """Transforme un message Gmail brut en GmailMessage."""
    headers = {h["name"]: h["value"] for h in raw.get("payload", {}).get("headers", [])}

    subject     = headers.get("Subject")
    sender      = headers.get("From")
    date_str    = headers.get("Date")
    received_at = None

    # Parse la date en ISO 8601
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


# ── Fonction principale ──────────────────────────────────────

def fetch_emails_by_label(label_name: str = LABEL) -> list[GmailMessage]:
    """
    Récupère tous les mails d'un libellé Gmail et les retourne
    sous forme de liste de GmailMessage.
    """
    creds = get_credentials()
    if not creds:
        raise PermissionError("Non authentifié. Lance d'abord GET /gmail/auth")

    service = build("gmail", "v1", credentials=creds)

    # 1. Résoudre l'ID du libellé depuis son nom
    labels_response = service.users().labels().list(userId="me").execute()
    label_id = next(
        (l["id"] for l in labels_response.get("labels", [])
         if l["name"].lower() == label_name.lower()),
        None
    )
    if not label_id:
        raise ValueError(f"Libellé '{label_name}' introuvable dans Gmail")

    # 2. Lister les messages du libellé
    messages_response = service.users().messages().list(
        userId="me",
        labelIds=[label_id],
        maxResults=MAX_RESULTS
    ).execute()

    message_ids = messages_response.get("messages", [])
    results     = []

    # 3. Récupérer chaque message en détail
    for msg in message_ids:
        raw = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()
        results.append(_parse_message(raw, label_name))

    return results