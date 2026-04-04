import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
# CRITIQUE : Importe EXACTEMENT la même dépendance que ton routeur
from app.services.auth.dependency import get_current_user 
from app.models.user import User

client = TestClient(app)

def test_scrape_stream_limited(monkeypatch):
    """Vérifie que le flux de scraping renvoie bien nos 5 entreprises simulées."""
    
    # 1. OVERRIDE de l'AUTH (indispensable ici pour éviter le 401)
    def mock_user():
        return User(
            google_id="google_123", 
            email="test@test.com", 
            name="Test",
            access_token="fake_access_token",  # Ajouté
            refresh_token="fake_refresh_token", # Ajouté
            token_expiry="2099-01-01T00:00:00" # Ajouté (format string ou datetime selon ton modèle)
        )
    
    app.dependency_overrides[get_current_user] = mock_user

    # 2. MOCK du SERVICE de SCRAPING
    def mock_stream_scraping(cities, user_id, repo):
        yield {"type": "phase", "phase": "scraping"}
        for i in range(1, 6):
            yield {"type": "company", "company": f"Entreprise Test {i}"}
        yield {"type": "done", "total": 5}

    monkeypatch.setattr("app.routers.scraping.stream_scraping", mock_stream_scraping)
    
    # 3. MOCK du REPO (pour éviter Mongo)
    monkeypatch.setattr("app.routers.scraping.JobRepository", lambda: object())

    try:
        # 4. REQUÊTE
        with client.stream("GET", "/scraping/stream?cities=Toulouse") as response:
            assert response.status_code == 200
            # On utilise "in" pour éviter les erreurs de charset utf-8
            assert "text/event-stream" in response.headers["content-type"]
            
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line.replace("data: ", "")))

            # 5. ASSERTIONS
            assert len([e for e in events if e["type"] == "company"]) == 5
            assert events[-1]["type"] == "done"

    finally:
        # On nettoie TOUJOURS les overrides après le test
        app.dependency_overrides.clear()