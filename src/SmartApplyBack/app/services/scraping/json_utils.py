# app/services/csv_utils.py

import os
import json

FIELDNAMES = ["nom", "domaine", "ville", "email", "secteur"]


def save_to_json(companies: list, filename: str) -> None:
    """
    Sauvegarde les entreprises dans un fichier JSON.
    Écrase le fichier à chaque appel — toujours à jour.

    Paramètres :
        companies : liste complète de dicts à sauvegarder
        filename  : chemin du fichier JSON de sortie
    """
    if not companies:
        return

    # Force l'extension .json
    filename = os.path.splitext(filename)[0] + ".json"

    with open(filename, mode="w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"💾 {len(companies)} entreprises sauvegardées dans '{filename}'")


def load_from_json(filename: str) -> list:
    """
    Charge les entreprises depuis un JSON existant.

    Paramètres :
        filename : chemin du fichier JSON

    Retourne :
        Liste de dicts représentant les entreprises.
    """
    filename = os.path.splitext(filename)[0] + ".json"

    if not os.path.exists(filename):
        print(f"📂 Aucun fichier existant : '{filename}'")
        return []

    with open(filename, mode="r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"📂 {len(companies)} entreprises chargées depuis '{filename}'")
    return companies