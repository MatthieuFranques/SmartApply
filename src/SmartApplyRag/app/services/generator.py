import json
import re

import ollama

from app.config import OLLAMA_HOST, COLLECTIONS
from app.services.indexer import index_letter
from app.services.prompts import (
    build_analysis_prompt,
    build_contact_form_prompt,
    build_header,
    build_letter_prompt,
)
from app.services.retriever import get_letter_context

_client = ollama.Client(host=OLLAMA_HOST)


def determine_mode(company: dict) -> str:
    if company.get("job_offers"):
        return "letter"
    if company.get("contact_form") and not company.get("job_offers"):
        return "contact"
    return "letter"


def _chat(model: str, prompt: str, temperature: float, max_tokens: int) -> str:
    print(f"[_chat] calling ollama model={model} host={OLLAMA_HOST}", flush=True)
    try:
        resp = _client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        print(f"[_chat] SUCCESS len={len(resp.message.content)}", flush=True)
        return resp.message.content.strip()
    except Exception as e:
        print(f"[_chat] EXCEPTION type={type(e).__name__} msg={e}", flush=True)
        raise


def generate_letter(
    company: dict,
    profile: dict,
    model: str,
    reference_letter: str = "",
    user_id: str = "default",
) -> str:
    rag_context = {}
    try:
        rag_context = get_letter_context(company)
    except Exception:
        pass

    analysis = _chat(
        model,
        build_analysis_prompt(company, profile, rag_context.get("cv_chunks")),
        temperature=0.3,
        max_tokens=500,
    )
    body = _chat(
        model,
        build_letter_prompt(company, profile, analysis, reference_letter, rag_context),
        temperature=0.7,
        max_tokens=750,
    )

    letter = f"{build_header(profile)}\n\n{body}"

    try:
        mode = "letter_targeted" if company.get("job_offers") else "letter_spontaneous"
        index_letter(letter, company, mode, user_id)
    except Exception:
        pass

    return letter


def generate_contact_form(
    company: dict,
    profile: dict,
    model: str,
    user_id: str = "default",
) -> dict:
    raw = _chat(
        model,
        build_contact_form_prompt(company, profile),
        temperature=0.5,
        max_tokens=600,
    )
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "error": "JSON invalide — à corriger manuellement"}
