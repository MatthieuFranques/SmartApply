from fastapi import Depends, HTTPException, Cookie
from typing import Optional

from app.services.auth.jwt_handler import decode_jwt
from app.repositories.user_repository import UserRepository
from app.models.user import User


async def get_current_user(session: Optional[str] = Cookie(None)) -> User:
    """
    Dependency injectable partout.
    Lit le cookie 'session' → décode JWT → retourne User depuis MongoDB.
    """
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Non authentifié → GET /gmail/auth"
        )

    google_id = decode_jwt(session)
    if not google_id:
        raise HTTPException(
            status_code=401,
            detail="Session invalide ou expirée → GET /gmail/auth"
        )

    user = UserRepository().find_by_google_id(google_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur introuvable"
        )

    return user