import os
from datetime import datetime, timedelta
import requests as http_requests

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI")


def get_auth_url() -> str:
    import urllib.parse
    params = {
        "client_id":              _CLIENT_ID.strip(),
        "redirect_uri":           _REDIRECT_URI,
        "response_type":          "code",
        "scope":                  " ".join(SCOPES),
        "access_type":            "offline",
        "include_granted_scopes": "true",
        "prompt":                 "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_for_user(code: str) -> tuple[dict, dict]:
    token_resp = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code":          code,
            "client_id":     _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
            "redirect_uri":  _REDIRECT_URI,
            "grant_type":    "authorization_code",
        },
        timeout=10,
    )
    token_resp.raise_for_status()
    token_data = token_resp.json()

    user_info_resp = http_requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )
    user_info_resp.raise_for_status()

    expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
    tokens = {
        "access_token":  token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "expiry":        expiry,
        "scopes":        token_data.get("scope", "").split(),
    }
    return user_info_resp.json(), tokens
