# ============================================================
# generator.py
# Génération via Ollama + sauvegarde
# ============================================================

import json
import re
from pathlib import Path

import ollama

from app.services.generate_letter.generate_letter_config import PROFILE
from app.services.generate_letter.generate_letter_prompts import build_analysis_prompt, build_letter_prompt, build_contact_form_prompt


def build_header(profile: dict) -> str:
    return (
        f"{profile['prenom_nom']}\n"
        f"{profile['titre']}\n"
        f"{profile['telephone']} | {profile['email']}\n"
        f"Portfolio : {profile['portfolio']}\n"
        f"GitHub : {profile['github']}"
    )


def slug(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def load_json(filepath: str) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def check_ollama() -> bool:
    try:
        ollama.list()
        return True
    except Exception:
        return False


def _chat(model: str, prompt: str, temperature: float, max_tokens: int) -> str:
    """Wrapper Ollama pour éviter la répétition."""
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": temperature, "num_predict": max_tokens},
    )
    return resp["message"]["content"].strip()


def generate_letter(company: dict, model: str, profile: dict | None = None, reference_letter: str = "") -> str:
    """
    Génération en 2 passes :
      Passe 1 (0.3) — analyse rigoureuse profil vs entreprise
      Passe 2 (0.7) — rédaction fluide basée sur l'analyse

    Args:
        profile:          user profile dict; falls back to hardcoded PROFILE if None or empty
        reference_letter: user's reference letter; falls back to default if empty
    """
    p        = profile if profile and profile.get("prenom_nom") else PROFILE
    analysis = _chat(model, build_analysis_prompt(company, p), 0.3, 500)
    body     = _chat(model, build_letter_prompt(company, p, analysis, reference_letter), 0.7, 750)
    return f"{build_header(p)}\n\n{body}"


def generate_contact_form(company: dict, model: str, profile: dict | None = None) -> dict:
    """
    Génère le contenu JSON pour remplir un formulaire de contact.
    Utilisé quand pas d'offre pertinente mais formulaire détecté.
    """
    p   = profile if profile and profile.get("prenom_nom") else PROFILE
    raw = _chat(model, build_contact_form_prompt(company, p), 0.5, 600)

    # Nettoyage du JSON généré
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "error": "JSON invalide — à corriger manuellement"}


def determine_mode(company: dict) -> str:
    """
    Détermine le mode de génération selon les données enrichies :
    - 'letter'  → offre(s) pertinente(s) ou pas de contact
    - 'contact' → formulaire de contact détecté, pas d'offre
    """
    has_offers  = bool(company.get("job_offers"))
    has_contact = bool(company.get("contact_form"))

    if has_offers:
        return "letter"
    if has_contact and not has_offers:
        return "contact"
    return "letter"  # Par défaut : candidature spontanée


def save_letter(text: str, company_name: str, output_dir: Path) -> Path:
    filepath = output_dir / f"lettre_{slug(company_name)}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    return filepath


def save_contact_form(data: dict, company_name: str, output_dir: Path) -> Path:
    filepath = output_dir / f"contact_{slug(company_name)}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath