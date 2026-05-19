import re
from pathlib import Path

from app.config import COLLECTIONS, DEFAULT_USER_ID, INBOX_PATH
from app.services.indexer import index_reference_letter
from app.services.vector_store import upsert

CV_DIR      = INBOX_PATH / "cvs"
LETTERS_DIR = INBOX_PATH / "letters"

CV_EXTENSIONS     = {".pdf", ".txt"}
LETTER_EXTENSIONS = {".txt", ".md", ".pdf"}

# Détecte les titres de sections courantes dans un CV FR/EN
_SECTION_RE = re.compile(
    r"(expériences?\s+professionnelles?|expériences?|experience|parcours"
    r"|compétences?\s+techniques?|compétences?|skills?|technologies"
    r"|formation|diplôme|education|études"
    r"|projets?\s+personnels?|projets?|réalisations?|projects?"
    r"|soft\s+skills?|qualités|langues?|profil|résumé|summary)",
    re.IGNORECASE,
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip()).strip("_")


def extract_text(filepath: Path) -> str:
    if filepath.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(filepath))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return filepath.read_text(encoding="utf-8", errors="ignore")


def _chunk_cv(text: str, filename_slug: str, user_id: str) -> list[tuple[str, str, dict]]:
    """Découpe le CV en chunks par section ou par paragraphe."""
    parts = _SECTION_RE.split(text)
    chunks: list[tuple[str, str, dict]] = []

    if len(parts) > 1:
        i = 1
        while i < len(parts):
            header  = parts[i].strip()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if content and len(content) > 40:
                doc_id = f"{user_id}_cv_{filename_slug}_{_slug(header)}"
                chunks.append((
                    doc_id,
                    f"{header}\n{content}",
                    {"chunk_type": header.lower(), "source": filename_slug, "user_id": user_id},
                ))
            i += 2

    if not chunks:
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if len(p.strip()) > 60]
        for idx, para in enumerate(paragraphs):
            doc_id = f"{user_id}_cv_{filename_slug}_{idx}"
            chunks.append((
                doc_id,
                para,
                {"chunk_type": "paragraph", "source": filename_slug, "user_id": user_id},
            ))

    return chunks


def ingest_cv_file(filepath: Path, user_id: str = DEFAULT_USER_ID) -> int:
    text = extract_text(filepath)
    filename_slug = _slug(filepath.stem)
    chunks = _chunk_cv(text, filename_slug, user_id)

    for doc_id, chunk_text, meta in chunks:
        upsert(COLLECTIONS["cv_chunks"], doc_id, chunk_text, meta)

    return len(chunks)


def ingest_letter_file(filepath: Path, user_id: str = DEFAULT_USER_ID) -> str:
    text   = extract_text(filepath)
    source = _slug(filepath.stem)
    return index_reference_letter(text, source, company_type="manual")


def ingest_inbox(user_id: str = DEFAULT_USER_ID) -> dict:
    CV_DIR.mkdir(parents=True, exist_ok=True)
    LETTERS_DIR.mkdir(parents=True, exist_ok=True)

    results: dict = {"cvs": [], "letters": [], "errors": []}

    for filepath in sorted(CV_DIR.iterdir()):
        if filepath.suffix.lower() not in CV_EXTENSIONS:
            continue
        try:
            count = ingest_cv_file(filepath, user_id)
            results["cvs"].append({"file": filepath.name, "chunks_indexed": count})
        except Exception as e:
            results["errors"].append({"file": filepath.name, "error": str(e)})

    for filepath in sorted(LETTERS_DIR.iterdir()):
        if filepath.suffix.lower() not in LETTER_EXTENSIONS:
            continue
        try:
            doc_id = ingest_letter_file(filepath, user_id)
            results["letters"].append({"file": filepath.name, "doc_id": doc_id})
        except Exception as e:
            results["errors"].append({"file": filepath.name, "error": str(e)})

    return results
