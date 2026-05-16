import json
import re

import ollama


def extract_pdf_text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader
    import io
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_cv_profile(cv_text: str, model: str = "mistral") -> dict:
    prompt = f"""Tu es un parseur de CV expert. Extrais les informations du CV ci-dessous.
Réponds UNIQUEMENT en JSON valide, sans markdown ni explication.

CV:
{cv_text[:3000]}

Format JSON attendu:
{{
  "prenom_nom":   "Prénom Nom",
  "titre":        "Développeur .NET / Fullstack",
  "email":        "email@example.com",
  "telephone":    "+33 6 ...",
  "ville":        "Ville",
  "portfolio":    "https://...",
  "github":       "https://github.com/...",
  "diplome":      "Master Informatique",
  "ecole":        "Nom de l'école",
  "annee":        "2024",
  "experiences":  "Description concise des expériences principales",
  "projet_phare": "Description du projet le plus important",
  "competences":  "Tech1, Tech2, Tech3...",
  "soft_skills":  "Communication, Autonomie...",
  "recherche":    "Poste recherché et contexte"
}}"""

    try:
        resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1, "num_predict": 600},
        )
        raw = resp["message"]["content"]
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        raise RuntimeError(f"Ollama indisponible : {e}") from e


def suggest_pipeline_config(profile: dict, model: str = "mistral") -> dict:
    profile_summary = (
        f"Diplôme: {profile.get('diplome', '')} — {profile.get('ecole', '')}\n"
        f"Compétences: {profile.get('competences', '')}\n"
        f"Recherche: {profile.get('recherche', '')}\n"
        f"Ville: {profile.get('ville', '')}"
    )

    prompt = f"""Tu es un expert en recherche d'emploi tech en France/Belgique.
Analyse ce profil et suggère une configuration optimale pour un pipeline de recherche d'entreprises.
Réponds UNIQUEMENT en JSON valide, sans markdown ni explication.

Profil:
{profile_summary}

Format JSON attendu:
{{
  "cities":        ["Ville1", "Ville2"],
  "sectors":       ["Secteur1", "Secteur2", "Secteur3"],
  "keyword_match": "any",
  "max_results":   100,
  "reasoning":     "Explication courte (1-2 phrases) de tes choix"
}}

Villes disponibles: Paris, Lyon, Toulouse, Bordeaux, Nantes, Lille, Strasbourg, Montpellier, Nice, Rennes, Grenoble, Marseille, Bruxelles, Luxembourg
Secteurs possibles: SaaS, Fintech, Deeptech, Cybersécurité, E-commerce, Gaming, Medtech, EdTech, Consulting, Agence, ESN, Industriel, Startup"""

    try:
        resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 400},
        )
        raw = resp["message"]["content"]
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
    except Exception:
        return {}
