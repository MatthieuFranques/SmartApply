"""Router tests for /candidatures (list, status, sync, reset)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.job_applications import SyncResult
from app.routers import job_applications as ja_router
from app.routers.job_applications import get_repo
from app.services.auth.dependency import get_current_user
from tests.conftest import FAKE_USER


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def ja_client(repo):
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_candidatures_all(ja_client, repo):
    repo.find_by_user.return_value = [
        {"entreprise": "Acme", "statut": "Entretien"},
        {"entreprise": "Globex", "statut": "Refusé"},
    ]
    resp = ja_client.get("/candidatures")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_candidatures_filtered_by_statut(ja_client, repo):
    repo.find_by_user.return_value = [
        {"entreprise": "Acme", "statut": "Entretien"},
        {"entreprise": "Globex", "statut": "Refusé"},
    ]
    resp = ja_client.get("/candidatures", params={"statut": "Entretien"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1 and body[0]["entreprise"] == "Acme"


def test_sync_status(ja_client, repo):
    repo.get_last_sync.return_value = datetime(2025, 5, 1, tzinfo=timezone.utc)
    repo.find_by_user.return_value = [{"x": 1}]
    resp = ja_client.get("/candidatures/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_en_cache"] == 1
    assert data["jamais_synchronise"] is False
    assert data["derniere_sync"].startswith("2025-05-01")


def test_sync_success(ja_client, repo):
    result = SyncResult(
        total_analyses=3, nouvelles=2, mises_a_jour=1,
        ignorees=0, sans_poste=0, derniere_sync="2025-05-01T00:00:00",
    )
    with patch.object(ja_router, "sync_candidatures", return_value=result):
        resp = ja_client.post("/candidatures/sync")
    assert resp.status_code == 200
    assert resp.json()["nouvelles"] == 2


def test_sync_permission_error_returns_401(ja_client, repo):
    with patch.object(ja_router, "sync_candidatures", side_effect=PermissionError):
        resp = ja_client.post("/candidatures/sync")
    assert resp.status_code == 401


def test_reset(ja_client, repo):
    resp = ja_client.delete("/candidatures/reset")
    assert resp.status_code == 200
    repo.delete_by_user.assert_called_once_with("google_123")
