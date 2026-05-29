"""Tests for the Ollama embedder (client mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services import embedder


def test_embed_text_returns_vector():
    resp = MagicMock()
    resp.embeddings = [[0.1, 0.2, 0.3]]
    with patch.object(embedder._client, "embed", return_value=resp):
        out = embedder.embed_text("  some text  ")
    assert out == [0.1, 0.2, 0.3]


def test_embed_text_failure_raises_runtime():
    with patch.object(embedder._client, "embed", side_effect=Exception("not pulled")):
        with pytest.raises(RuntimeError, match="Embedding failed"):
            embedder.embed_text("x")


def test_check_embed_model_true():
    models = MagicMock()
    m = MagicMock()
    m.model = "nomic-embed-text:latest"
    models.models = [m]
    with patch.object(embedder._client, "list", return_value=models):
        assert embedder.check_embed_model() is True


def test_check_embed_model_false_on_error():
    with patch.object(embedder._client, "list", side_effect=Exception("down")):
        assert embedder.check_embed_model() is False
