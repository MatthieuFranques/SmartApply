from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
import os

from app.services.gmail.gmail import (
    get_auth_url,
    save_token_from_code,
    fetch_emails_by_label,
)
from app.models.gmail import GmailMessage

router = APIRouter(prefix="/gmail", tags=["Gmail"])

GMAIL_LABEL = os.getenv("GMAIL_LABEL", "Candidatures")


# ── Étape 1 : rediriger vers Google pour autorisation ────────

@router.get("/auth", summary="Lancer l'authentification Gmail")
def gmail_auth():
    """
    Redirige vers la page de consentement Google.
    À appeler une seule fois pour générer le token.json.
    """
    auth_url = get_auth_url()
    return RedirectResponse(url=auth_url)


# ── Étape 2 : callback Google après consentement ─────────────

@router.get("/callback", summary="Callback OAuth Google")
def gmail_callback(code: str = Query(...)):
    """
    Google redirige ici après consentement.
    Sauvegarde le token dans token.json automatiquement.
    """
    try:
        save_token_from_code(code)
        return {"message": "Authentification réussie. Token sauvegardé."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Récupération des mails ────────────────────────────────────

@router.get(
    "/messages",
    response_model=list[GmailMessage],
    summary="Récupérer les mails d'un libellé"
)
def get_messages(label: str = Query(default=GMAIL_LABEL)):
    """
    Retourne tous les mails du libellé Gmail spécifié au format JSON.
    Utilise le libellé défini dans .env par défaut.
    """
    try:
        messages = fetch_emails_by_label(label)
        return messages
    except PermissionError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e) + " → Va sur http://localhost:8000/gmail/auth"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Statut auth ───────────────────────────────────────────────

@router.get("/status", summary="Vérifier si le token est valide")
def gmail_status():
    """Vérifie si un token Gmail valide est présent."""
    from app.services.gmail import get_credentials
    creds = get_credentials()
    if creds:
        return {"authenticated": True, "message": "Token valide ✅"}
    return {"authenticated": False, "message": "Non authentifié. Lance /gmail/auth"}