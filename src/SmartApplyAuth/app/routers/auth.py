import os
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.gmail.gmail import get_auth_url, exchange_code_for_user
from app.services.auth.jwt_handler import create_jwt
from app.services.auth.dependency import get_current_user
from app.repositories.user_repository import UserRepository
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/login")
def auth_login():
    return RedirectResponse(url=get_auth_url())


@router.get("/callback")
def auth_callback(code: str = Query(...)):
    try:
        user_info, tokens = exchange_code_for_user(code)

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

        jwt_token    = create_jwt(user.google_id)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
        is_prod      = os.getenv("ENV", "development") == "production"

        response = RedirectResponse(url=frontend_url)
        response.set_cookie(
            key      = "session",
            value    = jwt_token,
            httponly = True,
            samesite = "lax",
            secure   = is_prod,
            max_age  = 7 * 24 * 3600,
        )
        return response

    except Exception:
        error_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:4200')}?error=auth_failed"
        return RedirectResponse(url=error_url)


@router.get("/status")
def auth_status(current_user: User = Depends(get_current_user)):
    return {
        "authenticated": True,
        "email":         current_user.email,
        "name":          current_user.name,
    }


@router.post("/logout")
def auth_logout():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("session")
    return response