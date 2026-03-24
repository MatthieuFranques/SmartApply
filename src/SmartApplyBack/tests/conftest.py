import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.fixture
def client():
    """Client HTTP FastAPI pour tous les tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_company():
    """Entreprise fictive pour les tests."""
    return {
        "nom":               "TestCorp",
        "domaine":           "testcorp.fr",
        "ville":             "Toulouse",
        "secteur":           "IT",
        "company_size_hint": "50-200",
        "is_recruiting":     True,
        "scrape_status":     "ok",
        "job_offers":        [{"title": "Dev Python", "url": "https://testcorp.fr/jobs/1"}],
        "contact_form":      {"url": "https://testcorp.fr/contact"},
        "email":             "rh@testcorp.fr",
        "linkedin":          "https://linkedin.com/company/testcorp",
        "tech_stack":        ["Python", "FastAPI"],
    }


@pytest.fixture
def mock_gmail_message():
    """Mail fictif pour les tests Gmail."""
    return {
        "id":          "abc123",
        "subject":     "Votre candidature chez TestCorp",
        "sender":      "rh@testcorp.fr",
        "received_at": "2024-03-15T09:30:00+01:00",
        "body":        "Bonjour, nous avons bien reçu votre candidature.",
        "links":       ["https://testcorp.fr/jobs/1"],
        "label":       "Candidatures",
    }