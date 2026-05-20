import os

import httpx

RAG_URL     = os.getenv("RAG_URL",     "http://localhost:8001")
RAG_TIMEOUT = float(os.getenv("RAG_TIMEOUT", "120"))


def check_rag() -> bool:
    try:
        resp = httpx.get(f"{RAG_URL}/health", timeout=10)
        print(f"[check_rag] status={resp.status_code} url={RAG_URL}", flush=True)
        return resp.is_success
    except Exception as e:
        print(f"[check_rag] FAILED: {e}", flush=True)
        return False


def determine_mode(company: dict) -> str:
    if company.get("job_offers"):
        return "letter"
    if company.get("contact_form") and not company.get("job_offers"):
        return "contact"
    return "letter"


def generate_letter(
    company: dict,
    model: str,
    profile: dict | None = None,
    reference_letter: str = "",
    user_id: str = "default",
) -> str:
    url = f"{RAG_URL}/generate/letter"
    print(f"[generate_letter] POST {url} company={company.get('nom')} model={model}", flush=True)
    try:
        resp = httpx.post(
            url,
            json={
                "company":          company,
                "profile":          profile or {},
                "model":            model,
                "reference_letter": reference_letter,
                "user_id":          user_id,
            },
            timeout=RAG_TIMEOUT,
        )
        print(f"[generate_letter] RAG response status={resp.status_code}", flush=True)
        if not resp.is_success:
            print(f"[generate_letter] RAG error body={resp.text[:500]}", flush=True)
        resp.raise_for_status()
        return resp.json()["letter"]
    except Exception as e:
        print(f"[generate_letter] EXCEPTION type={type(e).__name__} msg={e}", flush=True)
        raise


def generate_contact_form(
    company: dict,
    model: str,
    profile: dict | None = None,
    user_id: str = "default",
) -> dict:
    resp = httpx.post(
        f"{RAG_URL}/generate/contact",
        json={
            "company": company,
            "profile": profile or {},
            "model":   model,
            "user_id": user_id,
        },
        timeout=RAG_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
