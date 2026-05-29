"""Tests for vector_store (chromadb + embedder mocked)."""

from unittest.mock import MagicMock, patch

from app.services import vector_store as vs


def test_upsert_calls_collection():
    col = MagicMock()
    with patch.object(vs, "embed_text", return_value=[0.1, 0.2]), \
         patch.object(vs, "_get_collection", return_value=col):
        vs.upsert("letters", "doc_1", "text", {"k": "v"})
    col.upsert.assert_called_once()
    _, kwargs = col.upsert.call_args
    assert kwargs["ids"] == ["doc_1"]
    assert kwargs["documents"] == ["text"]


def test_query_empty_collection_returns_empty():
    col = MagicMock()
    col.count.return_value = 0
    with patch.object(vs, "_get_collection", return_value=col):
        assert vs.query("letters", "q") == []


def test_query_returns_mapped_results():
    col = MagicMock()
    col.count.return_value = 2
    col.query.return_value = {
        "documents": [["doc a", "doc b"]],
        "metadatas": [[{"x": 1}, {"x": 2}]],
        "distances": [[0.1, 0.2]],
    }
    with patch.object(vs, "embed_text", return_value=[0.1]), \
         patch.object(vs, "_get_collection", return_value=col):
        out = vs.query("letters", "q", k=2)
    assert [r["text"] for r in out] == ["doc a", "doc b"]
    assert out[0]["distance"] == 0.1


def test_collection_count():
    col = MagicMock()
    col.count.return_value = 5
    with patch.object(vs, "_get_collection", return_value=col):
        assert vs.collection_count("letters") == 5


def test_collection_count_error_returns_zero():
    with patch.object(vs, "_get_collection", side_effect=RuntimeError("no db")):
        assert vs.collection_count("letters") == 0
