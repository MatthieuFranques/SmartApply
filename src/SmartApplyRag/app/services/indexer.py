import re
import time

from app.config import COLLECTIONS
from app.services.vector_store import upsert


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip()).strip("_")


def index_letter(letter_text: str, company: dict, mode: str, user_id: str = "default") -> str:
    company_slug = _slug(company.get("nom", "unknown"))
    doc_id = f"{user_id}_{company_slug}_{int(time.time())}"

    upsert(
        COLLECTIONS["letters"],
        doc_id,
        letter_text,
        {
            "company_name": company.get("nom", ""),
            "sector":       company.get("secteur", ""),
            "city":         company.get("ville", ""),
            "mode":         mode,
            "user_id":      user_id,
            "timestamp":    int(time.time()),
            "tech":         ", ".join(company.get("tech_keywords", [])[:8]),
        },
    )
    return doc_id


def index_cv_profile(profile: dict, user_id: str = "default") -> list[str]:
    chunks = {
        "experiences":    profile.get("experiences", ""),
        "project":        profile.get("projet_phare", ""),
        "skills":         profile.get("competences", ""),
        "soft_recherche": f"{profile.get('soft_skills', '')} {profile.get('recherche', '')}".strip(),
    }

    ids = []
    for chunk_key, chunk_text in chunks.items():
        if not chunk_text.strip():
            continue
        doc_id = f"{user_id}_cv_{chunk_key}"
        upsert(
            COLLECTIONS["cv_chunks"],
            doc_id,
            chunk_text,
            {"user_id": user_id, "chunk_type": chunk_key, "name": profile.get("prenom_nom", "")},
        )
        ids.append(doc_id)
    return ids


def index_company(company: dict) -> str:
    company_slug = _slug(company.get("nom", "unknown"))

    text = " ".join(filter(None, [
        company.get("nom", ""),
        company.get("secteur", ""),
        (company.get("description") or company.get("about_text", ""))[:400],
        " ".join(company.get("tech_keywords", [])),
        " ".join(company.get("key_phrases", [])),
    ]))

    upsert(
        COLLECTIONS["companies"],
        company_slug,
        text,
        {
            "company_name": company.get("nom", ""),
            "sector":       company.get("secteur", ""),
            "city":         company.get("ville", ""),
            "tech":         ", ".join(company.get("tech_keywords", [])[:8]),
        },
    )
    return company_slug


def index_reference_letter(letter_text: str, source: str, company_type: str = "generic") -> str:
    doc_id = f"ref_{_slug(source)}_{int(time.time())}"
    upsert(
        COLLECTIONS["references"],
        doc_id,
        letter_text,
        {"source": source, "company_type": company_type, "timestamp": int(time.time())},
    )
    return doc_id
