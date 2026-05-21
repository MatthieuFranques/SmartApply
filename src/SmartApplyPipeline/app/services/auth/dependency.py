import os
from typing import Optional
from fastapi import Cookie, HTTPException
from pydantic import BaseModel
import httpx


class AuthUser(BaseModel):
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None


async def get_current_user(session: Optional[str] = Cookie(None)) -> AuthUser:
    if not session:
        raise HTTPException(status_code=401, detail="Non authentifié → GET /gmail/auth")

    gmail_url = os.getenv("GMAIL_URL", "http://gmail:8004")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{gmail_url}/auth/me",
                cookies={"session": session},
                timeout=5.0,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée → GET /gmail/auth")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Auth service error")

    return AuthUser(**response.json())
