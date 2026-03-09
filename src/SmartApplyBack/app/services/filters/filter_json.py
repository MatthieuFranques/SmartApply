"""
filter_json.py
--------------
Lecture et écriture JSON partagées entre prefilter.py et deep_filter.py.
Remplace les fonctions load_csv / save_csv dupliquées dans les deux fichiers.
"""

import os
import json

PREFILTER_FIELDS = [
    "prescore", "nom", "domaine", "ville", "email",
    "secteur", "site_title", "site_desc", "it_keywords",
]

DEEP_FILTER_FIELDS = [
    "deep_score", "nom", "domaine", "ville", "email",
    "secteur", "has_mx", "mx_provider",
    "has_careers", "it_jobs_found", "careers_url", "site_title",
]

ELIMINATED_FIELDS = [
    "prescore", "nom", "domaine", "ville", "secteur", "raison_filtre",
]


def load_json(filename: str) -> list:
    """
    Charge un JSON et retourne une liste de dicts.
    Retourne une liste vide si le fichier est introuvable.
    """
    filename = os.path.splitext(filename)[0] + ".json"
    if not os.path.exists(filename):
        print(f"⚠️  Fichier introuvable : {filename}")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        rows = json.load(f)
    print(f"📂 {len(rows)} entreprises chargées depuis '{filename}'")
    return rows


def save_json(companies: list, filename: str, fieldnames: list = None) -> None:
    """
    Sauvegarde une liste de dicts dans un JSON.
    Crée les dossiers parents si nécessaire.
    fieldnames : si fourni, filtre les clés à garder (optionnel).
    """
    if not companies:
        return

    filename = os.path.splitext(filename)[0] + ".json"
    os.makedirs(os.path.dirname(filename), exist_ok=True) if os.path.dirname(filename) else None

    # Filtre les champs si fieldnames est fourni
    if fieldnames:
        companies = [{k: c.get(k, "") for k in fieldnames} for c in companies]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"💾 {len(companies)} entreprises → '{filename}'")