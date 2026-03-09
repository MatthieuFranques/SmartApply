import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import csv
from scraping_config import OUTPUT_CSV

FIELDNAMES = ["nom", "domaine", "ville", "email", "secteur"]


def save_to_csv(companies: list, filename: str = OUTPUT_CSV) -> None:
    """
    Sauvegarde les entreprises dans un fichier CSV.
    Écrase le fichier à chaque appel — toujours à jour.

    Paramètres :
        companies : liste complète de dicts à sauvegarder
        filename  : chemin du fichier CSV de sortie
    """
    if not companies:
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(companies)

    print(f"💾 {len(companies)} entreprises sauvegardées dans '{filename}'")


def load_from_csv(filename: str = OUTPUT_CSV) -> list:
    """
    Charge les entreprises depuis un CSV existant pour relancer
    la génération de lettres sans refaire le scraping.

    Paramètres :
        filename : chemin du fichier CSV

    Retourne :
        Liste de dicts représentant les entreprises.
    """
    companies = []

    with open(filename, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            companies.append(dict(row))

    print(f"📂 {len(companies)} entreprises chargées depuis '{filename}'")
    return companies
