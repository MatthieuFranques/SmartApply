import os
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError

ALGORITHM   = "HS256"
EXPIRE_DAYS = 7

def get_secret_key() -> str:
    return os.getenv("JWT_SECRET_KEY") or "ci_test_fallback_key_32_chars_min"

def create_jwt(google_id: str) -> str:
    payload = {
        "sub": google_id,
        "exp": datetime.utcnow() + timedelta(days=EXPIRE_DAYS),
    }
    # On appelle la fonction ici
    return jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM)

def decode_jwt(token: str) -> Optional[str]:
    try:
        # On appelle la fonction ici aussi
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        return payload.get("sub")
    except (JWTError, Exception): # On attrape tout pour être safe en CI
        return None