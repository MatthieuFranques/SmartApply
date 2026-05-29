"""Tests for the inbox ingestor (file parsing + chunking; upsert mocked)."""

from pathlib import Path
from unittest.mock import patch

from app.services import ingestor


def test_slug():
    assert ingestor._slug("CV Jane Doe!.pdf") == "cv_jane_doe_pdf"


def test_extract_text_txt(tmp_path):
    f = tmp_path / "cv.txt"
    f.write_text("hello world", encoding="utf-8")
    assert ingestor.extract_text(f) == "hello world"


def test_chunk_cv_by_section():
    text = "Expériences\nWorked at Acme for five years building backend services and APIs."
    chunks = ingestor._chunk_cv(text, "cv_jane", "u1")
    assert len(chunks) >= 1
    doc_id, content, meta = chunks[0]
    assert doc_id.startswith("u1_cv_cv_jane_")
    assert meta["user_id"] == "u1"


def test_chunk_cv_paragraph_fallback():
    text = ("A" * 80) + "\n\n" + ("B" * 80)  # no section headers, two long paragraphs
    chunks = ingestor._chunk_cv(text, "cv_jane", "u1")
    assert len(chunks) == 2
    assert all(m["chunk_type"] == "paragraph" for _, _, m in chunks)


def test_ingest_cv_file_counts_chunks(tmp_path):
    f = tmp_path / "cv.txt"
    f.write_text("Compétences\nPython, Docker, SQL and a lot of relevant tech experience.", encoding="utf-8")
    with patch.object(ingestor, "upsert") as mock_upsert:
        count = ingestor.ingest_cv_file(f, "u1")
    assert count >= 1
    assert mock_upsert.call_count == count


def test_ingest_letter_file(tmp_path):
    f = tmp_path / "letter.txt"
    f.write_text("Dear hiring manager...", encoding="utf-8")
    with patch.object(ingestor, "index_reference_letter", return_value="ref_1") as mock_ref:
        out = ingestor.ingest_letter_file(f, "u1")
    assert out == "ref_1"
    mock_ref.assert_called_once()


def test_ingest_inbox_processes_both_dirs(tmp_path, monkeypatch):
    cv_dir = tmp_path / "cvs"
    letters_dir = tmp_path / "letters"
    cv_dir.mkdir()
    letters_dir.mkdir()
    (cv_dir / "cv.txt").write_text("Skills\nPython Docker SQL and more relevant experience here.", encoding="utf-8")
    (cv_dir / "ignore.jpg").write_text("x", encoding="utf-8")  # wrong extension
    (letters_dir / "ref.txt").write_text("Dear team...", encoding="utf-8")

    monkeypatch.setattr(ingestor, "CV_DIR", cv_dir)
    monkeypatch.setattr(ingestor, "LETTERS_DIR", letters_dir)

    with patch.object(ingestor, "upsert"), \
         patch.object(ingestor, "index_reference_letter", return_value="ref_1"):
        results = ingestor.ingest_inbox("u1")

    assert len(results["cvs"]) == 1
    assert len(results["letters"]) == 1
    assert results["errors"] == []
