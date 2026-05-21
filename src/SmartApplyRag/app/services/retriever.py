from app.config import COLLECTIONS, TOP_K_LETTERS, TOP_K_CV, TOP_K_REFS
from app.services.vector_store import query


def _company_query(company: dict) -> str:
    return " ".join(filter(None, [
        company.get("nom", ""),
        company.get("secteur", ""),
        company.get("ville", ""),
        *company.get("tech_keywords", [])[:8],
        *company.get("job_keywords",  [])[:8],
        (company.get("description") or "")[:200],
    ]))


def _tech_query(company: dict) -> str:
    return " ".join(filter(None, [
        *company.get("tech_keywords", [])[:10],
        *company.get("job_keywords",  [])[:10],
        company.get("secteur", ""),
    ]))


def get_similar_letters(company: dict, k: int = TOP_K_LETTERS) -> list[str]:
    results = query(COLLECTIONS["letters"], _company_query(company), k)
    return [r["text"] for r in results]


def get_relevant_cv_chunks(company: dict, k: int = TOP_K_CV) -> list[str]:
    results = query(COLLECTIONS["cv_chunks"], _tech_query(company), k)
    return [r["text"] for r in results]


def get_reference_letters(company: dict, k: int = TOP_K_REFS) -> list[str]:
    results = query(COLLECTIONS["references"], _company_query(company), k)
    return [r["text"] for r in results]


def get_letter_context(
    company: dict,
    k_letters: int = TOP_K_LETTERS,
    k_cv: int = TOP_K_CV,
    k_refs: int = TOP_K_REFS,
) -> dict:
    similar_letters   = get_similar_letters(company, k_letters)
    cv_chunks         = get_relevant_cv_chunks(company, k_cv)
    reference_letters = get_reference_letters(company, k_refs)

    return {
        "similar_letters":   similar_letters,
        "cv_chunks":         cv_chunks,
        "reference_letters": reference_letters,
        "has_context":       any([similar_letters, cv_chunks, reference_letters]),
    }
