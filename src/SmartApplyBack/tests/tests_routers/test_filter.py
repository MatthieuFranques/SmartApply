import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth.dependency import get_current_user
from app.models.user import User

client = TestClient(app)

# 1. Mock de l'utilisateur
def override_get_current_user():
    return User(
        google_id="google_123",
        email="test@gmail.com",
        name="Test User",
        access_token="fake_access_token",
        refresh_token="fake_refresh_token",  # Ajouté
        token_expiry=3600,                   # Ajouté (un int ou float selon ton modèle)
        picture="https://example.com/p.jpg",  # Ajoute aussi picture et scopes si Pydantic râle encore
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )

app.dependency_overrides[get_current_user] = override_get_current_user

# 2. Données de simulation (Mocks)
class MockJob:
    def __init__(self, nom, domaine, stage):
        self.nom = nom
        self.domaine = domaine
        self.stage = stage
    def model_dump(self):
        return {"nom": self.nom, "domaine": self.domaine, "stage": self.stage}

class MockFilterRepository:
    def find_by_stage(self, user_id, stage):
        if stage == "scraping":
            # Pour le test du stream, on simule 1 job à filtrer
            return [MockJob("Entreprise A Scraper", "a.com", "scraping")]
        if stage == "deep":
            # Pour le test des résultats
            return [MockJob("Entreprise Filtrée", "b.com", "deep")]
        return []

# Simulation du service de pipeline (pour ne pas lancer les vrais appels API/Scraping)
def mock_stream_pipeline(*args, **kwargs):
    yield {"type": "phase", "phase": "filter", "status": "started"}
    yield {"type": "result", "company": "Entreprise A Scraper", "status": "kept"}
    yield {"type": "done", "total": 1}

# --- TESTS ---

def test_filter_results(monkeypatch):
    """Teste la récupération des résultats filtrés (stage 'deep')"""
    monkeypatch.setattr("app.routers.filter.JobRepository", MockFilterRepository)
    
    response = client.get("/filter/results")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nom"] == "Entreprise Filtrée"
    assert data[0]["stage"] == "deep"

def test_filter_stream_success(monkeypatch):
    """Teste le flux SSE du filtrage (Success scenario)"""
    monkeypatch.setattr("app.routers.filter.JobRepository", MockFilterRepository)
    # On mock le service de pipeline pour éviter les vrais calculs
    monkeypatch.setattr("app.routers.filter.stream_pipeline", mock_stream_pipeline)

    # On utilise client.stream pour les réponses StreamingResponse
    with client.stream("GET", "/filter/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # On lit les lignes du stream
        lines = [line for line in response.iter_lines() if line]
        
        # Vérification du premier événement
        assert "data: " in lines[0]
        event1 = json.loads(lines[0].replace("data: ", ""))
        assert event1["type"] == "phase"
        
        # Vérification du résultat
        event2 = json.loads(lines[1].replace("data: ", ""))
        assert event2["company"] == "Entreprise A Scraper"
        assert event2["status"] == "kept"

def test_filter_stream_empty(monkeypatch):
    """Teste le flux SSE quand il n'y a aucun job au stage 'scraping'"""
    class EmptyRepo:
        def find_by_stage(self, uid, stage): return []
        
    monkeypatch.setattr("app.routers.filter.JobRepository", EmptyRepo)

    with client.stream("GET", "/filter/stream") as response:
        lines = [line for line in response.iter_lines() if line]
        event = json.loads(lines[0].replace("data: ", ""))
        assert event["type"] == "error"
        assert "Aucun job à filtrer" in event["message"]