"""Router tests for /scraping (config + SSE stream)."""

from unittest.mock import MagicMock, patch

from app.routers import scraping as scraping_router


def test_scraping_config_no_auth(client):
    resp = client.get("/scraping/config")
    assert resp.status_code == 200
    body = resp.json()
    assert "default_sectors" in body
    assert "supported_cities" in body


def test_scraping_stream_emits_events(auth_client):
    def fake_stream(*args, **kwargs):
        yield {"type": "progress", "company": "Acme"}
        yield {"type": "done"}

    with patch.object(scraping_router, "JobRepository", return_value=MagicMock()), \
         patch.object(scraping_router, "stream_scraping", side_effect=fake_stream):
        resp = auth_client.get("/scraping/stream?cities=Toulouse")

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "Acme" in resp.text
    assert '"type": "done"' in resp.text


def test_scraping_stream_requires_auth(client):
    resp = client.get("/scraping/stream")
    assert resp.status_code == 401
