"""Test for the /health endpoint (covers main.py wiring)."""

from unittest.mock import patch

from app import main


def test_health_ok(client):
    with patch.object(main, "check_embed_model", return_value=True), \
         patch.object(main, "collection_count", return_value=0):
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["embed_model_ready"] is True
    assert "collections" in body


def test_health_degraded(client):
    with patch.object(main, "check_embed_model", return_value=False), \
         patch.object(main, "collection_count", return_value=0):
        resp = client.get("/health")
    assert resp.json()["status"] == "degraded"
