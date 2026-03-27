import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Test de la redirection Auth
def test_gmail_auth_redirect():
    """Vérifie que la route /auth redirige bien vers Google"""
    with patch("app.routers.gmail.get_auth_url") as mock_url:
        mock_url.return_value = "https://accounts.google.com/o/oauth2/auth?fake=true"
        response = client.get("/gmail/auth", follow_redirects=False)
        
        assert response.status_code == 303 or response.status_code == 307
        assert "accounts.google.com" in response.headers["location"]

# 2. Test du Callback (Succès)
def test_gmail_callback_success():
    """Vérifie que le callback sauvegarde le code et répond avec succès"""
    with patch("app.routers.gmail.save_token_from_code") as mock_save:
        response = client.get("/gmail/callback?code=fake_auth_code")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Authentification réussie. Token sauvegardé."}
        mock_save.assert_called_once_with("fake_auth_code")

# 3. Test du Callback (Erreur)
def test_gmail_callback_error():
    """Vérifie la gestion d'erreur si le code est invalide"""
    with patch("app.routers.gmail.save_token_from_code") as mock_save:
        mock_save.side_effect = Exception("Invalid Code")
        response = client.get("/gmail/callback?code=wrong_code")
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid Code"

# 4. Test Récupération Messages (Succès)
def test_get_messages_success():
    """Vérifie qu'on récupère bien une liste de messages si authentifié"""
    mock_messages = [
        {"id": "1", "threadId": "A", "snippet": "Hello", "subject": "Test", "sender": "me", "date": "2024", "body": "content"}
    ]
    with patch("app.routers.gmail.fetch_emails_by_label") as mock_fetch:
        mock_fetch.return_value = mock_messages
        response = client.get("/gmail/messages?label=INBOX")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["id"] == "1"

# 5. Test Récupération Messages (Non Authentifié - 401)
def test_get_messages_unauthorized():
    """Vérifie l'erreur 401 quand le service lève une PermissionError"""
    with patch("app.routers.gmail.fetch_emails_by_label") as mock_fetch:
        mock_fetch.side_effect = PermissionError("Token expired")
        response = client.get("/gmail/messages")
        
        assert response.status_code == 401
        assert "auth" in response.json()["detail"]

# 6. Test du Statut (Authentifié)
def test_gmail_status_authenticated():
    """Vérifie le statut quand le token est valide"""
    with patch("app.routers.gmail.get_credentials") as mock_creds:
        mock_creds.return_value = MagicMock() # Simule des crédentials valides
        response = client.get("/gmail/status")
        
        assert response.status_code == 200
        assert response.json()["authenticated"] is True

# 7. Test du Statut (Non Authentifié)
def test_gmail_status_unauthenticated():
    """Vérifie le statut quand le token est absent"""
    with patch("app.routers.gmail.get_credentials") as mock_creds:
        mock_creds.return_value = None
        response = client.get("/gmail/status")
        
        assert response.status_code == 200
        assert response.json()["authenticated"] is False