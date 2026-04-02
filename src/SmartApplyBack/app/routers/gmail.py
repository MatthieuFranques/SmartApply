from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import os

from app.services.gmail.gmail import get_auth_url, exchange_code_for_user, fetch_emails_by_label
from app.services.auth.jwt_handler import create_jwt
from app.services.auth.dependency import get_current_user
from app.repositories.user_repository import UserRepository
from app.models.gmail import GmailMessage
from app.models.user import User

router = APIRouter(prefix="/gmail", tags=["Gmail"])


@router.get("/auth")
def gmail_auth():
    return RedirectResponse(url=get_auth_url())


@router.get("/callback")
def gmail_callback(code: str = Query(...)):
    try:
        # 1. On échange le code contre les infos Google
        user_info, tokens = exchange_code_for_user(code)

        # 2. ON ENREGISTRE DANS LA BASE (C'est cette ligne qui remplit ta DB)
        user = UserRepository().upsert(
            google_id     = user_info["sub"],
            email         = user_info["email"],
            name          = user_info.get("name", "Utilisateur"),
            picture       = user_info.get("picture", ""),
            access_token  = tokens["access_token"],
            refresh_token = tokens["refresh_token"],
            token_expiry  = tokens["expiry"],
            scopes        = tokens["scopes"],
        )

        # 3. On crée le JWT pour la session
        jwt_token = create_jwt(user.google_id)
        
        # 4. On redirige vers Angular avec le cookie
        response = RedirectResponse(url="http://localhost:4200")
        
        response.set_cookie(
            key      = "session",
            value    = jwt_token,
            httponly = True,
            samesite = "lax",
            secure   = False,  # False car on est en HTTP local
            max_age  = 7 * 24 * 3600,
        )
        print(f"✅ Utilisateur {user.email} enregistré et redirigé.")
        return response

    except Exception as e:
        print(f"❌ Erreur lors du callback: {e}")
        return RedirectResponse(url="http://localhost:4200?error=auth_failed")



@router.get("/messages", response_model=list[GmailMessage])
def get_messages(
    label: str = Query(default=os.getenv("GMAIL_LABEL", "Candidatures")),
    current_user: User = Depends(get_current_user),    # ← protégé
):
    try:
        return fetch_emails_by_label(label, current_user.access_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def gmail_status(current_user: User = Depends(get_current_user)):
    return {
        "authenticated": True,
        "email":         current_user.email,
        "name":          current_user.name,
    }


@router.post("/logout")
def logout():
    response = JSONResponse({"message": "Déconnecté"})
    response.delete_cookie("session")
    return response