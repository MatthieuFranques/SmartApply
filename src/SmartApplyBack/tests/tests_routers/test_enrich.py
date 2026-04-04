import pytest
from fastapi.testclient import TestClient
from app.main import app  # Importe ton instance FastAPI
from app.services.auth.dependency import get_current_user
from app.repositories.job_repository import JobRepository
from app.models.user import User
from app.models.job import Job

# 1. Création du client de test
client = TestClient(app)

# 2. Mock de l'utilisateur connecté
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

# On remplace la dépendance réelle par notre version de test
app.dependency_overrides[get_current_user] = override_get_current_user

# 3. Mock du Repository
class MockJobRepository:
    # Dans tests/tests_routers/test_enrich.py
    def find_by_stage(self, user_id, stage):
        if stage == "enriched":
            return [
                Job(
                    user_id="google_123",  # Champ manquant
                    nom="Test Corp",
                    domaine="test.com",
                    secteur="Informatique",  # Champ manquant
                    stage="enriched",
                    ville="Toulouse"
                )
            ]
        return []

# --- TESTS ---

def test_get_enriched_results(monkeypatch):
    """Vérifie que la route /results renvoie bien une liste de jobs enrichis."""
    
    # On force l'utilisation du MockRepository au lieu du vrai
    monkeypatch.setattr("app.routers.enrich.JobRepository", MockJobRepository)

    response = client.get("/enrich/results")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["nom"] == "Test Corp"
    assert data[0]["stage"] == "enriched"

def test_enrich_stream_no_jobs(monkeypatch):
    """Vérifie le comportement du stream SSE quand il n'y a rien à traiter."""
    
    # Mock qui renvoie une liste vide pour le stage "deep"
    class EmptyRepo:
        def find_by_stage(self, uid, stage): return []
    
    monkeypatch.setattr("app.routers.enrich.JobRepository", EmptyRepo)

    # On utilise un contexte de streaming
    with client.stream("GET", "/enrich/stream") as response:
        assert response.status_code == 200
        # Lit le premier événement SSE
        first_event = next(response.iter_lines())
        assert "Aucun job à enrichir" in first_event