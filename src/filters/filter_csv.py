"""
filter_csv.py
-------------
Lecture et écriture CSV partagées entre prefilter.py et deep_filter.py.
Remplace les fonctions load_csv / save_csv dupliquées dans les deux fichiers.
"""

import os
import csv

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


def load_csv(filename: str) -> list:
    """
    Charge un CSV et retourne une liste de dicts.
    Retourne une liste vide si le fichier est introuvable.
    """
    if not os.path.exists(filename):
        print(f"⚠️  Fichier introuvable : {filename}")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    print(f"📂 {len(rows)} entreprises chargées depuis '{filename}'")
    return rows


def save_csv(companies: list, filename: str, fieldnames: list) -> None:
    """
    Sauvegarde une liste de dicts dans un CSV.
    Crée les dossiers parents si nécessaire.
    """
    if not companies:
        return
    os.makedirs(os.path.dirname(filename), exist_ok=True) if os.path.dirname(filename) else None
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(companies)
    print(f"💾 {len(companies)} entreprises → '{filename}'")
