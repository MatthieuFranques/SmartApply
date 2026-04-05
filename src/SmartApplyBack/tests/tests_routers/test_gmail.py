import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth.dependency import get_current_user
from app.models.user import User
import json

client = TestClient(app)

# --- MOCKS DES DÉPENDANCES ---

def override_get_current_user():
    return User(
        google_id="google_123",
        email="test@gmail.com",
        name="Test User",
        access_token="fake_access_token",
        refresh_token="fake_refresh_token",  # Ajouté
        token_expiry=3600,                   # Ajouté (un int ou float selon ton modèle)
        picture="http://example.com/p.jpg",  # Ajoute aussi picture et scopes si Pydantic râle encore
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )

# Mock pour simuler l'échange de code Google (Callback)
def mock_exchange_code(code):
    user_info = {"sub": "google_123", "email": "test@gmail.com", "name": "Test User"}
    tokens = {
        "access_token": "abc", 
        "refresh_token": "def", 
        "expiry": 3600, 
        "scopes": ["gmail.readonly"]
    }
    return user_info, tokens

# Mock du Repository pour éviter MongoDB
class MockUserRepository:
    def upsert(self, **kwargs):
        # On retourne un objet User simulé
        return User(**kwargs)

# --- TESTS ---

def test_gmail_auth_redirect():
    """Vérifie que /auth redirige bien vers Google."""
    response = client.get("/gmail/auth", follow_redirects=False)
    assert response.status_code == 307  # Temporary Redirect
    assert "accounts.google.com" in response.headers["location"]

def test_gmail_callback_success(monkeypatch):
    """Vérifie que le callback enregistre l'user et crée un cookie."""
    # On mock les appels externes et la DB
    monkeypatch.setattr("app.routers.gmail.exchange_code_for_user", mock_exchange_code)
    monkeypatch.setattr("app.routers.gmail.UserRepository", MockUserRepository)
    
    response = client.get("/gmail/callback?code=fake_code", follow_redirects=False)
    
    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:4200"
    # Vérification du cookie de session
    assert "session" in response.cookies

def test_gmail_status_authenticated():
    """Vérifie que /status renvoie les infos de l'user connecté."""
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    response = client.get("/gmail/status")
    assert response.status_code == 200
    assert response.json()["email"] == "test@gmail.com"
    assert response.json()["authenticated"] is True
    
    # Nettoyage pour les autres tests
    app.dependency_overrides = {}

def test_gmail_messages_error(monkeypatch):
    """Vérifie la gestion d'erreur si l'appel Gmail échoue."""
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # On simule une erreur lors de la récupération des emails
    def mock_fetch_error(*args):
        raise Exception("Google API Error")
    
    monkeypatch.setattr("app.routers.gmail.fetch_emails_by_label", mock_fetch_error)
    
    response = client.get("/gmail/messages?label=INBOX")
    assert response.status_code == 500
    assert "Google API Error" in response.json()["detail"]
    
    app.dependency_overrides = {}

def test_logout():
    """Vérifie que le logout supprime le cookie."""
    response = client.post("/gmail/logout")
    assert response.status_code == 200
    # Vérifie que le header demande la suppression du cookie
    # (Expires=Thu, 01 Jan 1970 00:00:00 GMT)
    assert 'session=""' in response.headers["set-cookie"]