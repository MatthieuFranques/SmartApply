import pytest
from fastapi.testclient import TestClient
from app.main import app  # Importe ton instance FastAPI

client = TestClient(app)

def test_gmail_auth_redirect():
    """Vérifie que la route /auth redirige bien vers Google"""
    response = client.get("/gmail/auth", follow_redirects=False)
    assert response.status_code == 307
    assert "accounts.google.com" in response.headers["location"]

def test_gmail_status():
    """Vérifie si le endpoint status répond correctement"""
    response = client.get("/gmail/status")
    assert response.status_code == 200
    assert "authenticated" in response.json()

def test_get_messages_unauthorized():
    """
    Vérifie que l'API renvoie une 401 si le token est absent ou invalide.
    Note: Ce test suppose que tu n'as pas encore de token.json valide.
    """
    # On force un libellé pour le test
    response = client.get("/gmail/messages?label=Candidatures")
    
    # Si le token n'existe pas, ton code est censé lever une PermissionError -> 401
    if response.status_code == 401:
        assert "auth" in response.json()["detail"]
    else:
        # Si tu es déjà connecté, il devrait renvoyer une liste (même vide)
        assert response.status_code == 200
        assert isinstance(response.json(), list)