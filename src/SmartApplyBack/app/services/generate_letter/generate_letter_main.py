"""
main.py
-------
Point d'entrée — génère les lettres de motivation via Ollama.

Usage:
    python main.py --input ../../results/be/enriched.json --output ../../results/be/letters/  
    python main.py --input enriched.json --output letters/
    python main.py --input enriched.json --output letters/ --model mistral
    python main.py --input enriched.json --output letters/ --company "Acme Corp"
    python main.py --input enriched.json --output letters/ --only-ok

Dépendances:
    pip install ollama tqdm
    + Ollama lancé avec : ollama serve
    + Modèle installé  : ollama pull mistral
"""

import argparse
import time
from pathlib import Path
from tqdm import tqdm

from app.services.generate_letter.generate_letter_generator import (
    generate_letter,
    generate_contact_form,
    determine_mode,
    save_letter,
    save_contact_form,
    load_json,
    check_ollama,
)


def format_duration(seconds: float) -> str:
    if seconds >= 60:
        m, s = divmod(int(seconds), 60)
        return f"{m}m{s:02d}s"
    return f"{seconds:.1f}s"


def main():
    parser = argparse.ArgumentParser(
        description="Génère lettres de motivation ou formulaires de contact via Ollama."
    )
    parser.add_argument("--input",    required=True,        help="JSON enrichi (enrich_main.py)")
    parser.add_argument("--output",   default="letters",    help="Dossier de sortie")
    parser.add_argument("--model",    default="mistral",    help="Modèle Ollama (défaut: mistral)")
    parser.add_argument("--company",  default=None,         help="Filtrer sur une entreprise")
    parser.add_argument("--only-ok",  action="store_true",  help="Ignorer les erreurs de scraping")
    args = parser.parse_args()

    if not check_ollama():
        print("❌ Ollama n'est pas accessible.")
        print("   Lance-le avec      : ollama serve")
        print("   Installe le modèle : ollama pull mistral")
        return

    companies = load_json(args.input)

    if args.only_ok:
        companies = [c for c in companies if c.get("scrape_status") == "ok"]
    if args.company:
        companies = [c for c in companies if args.company.lower() in c["nom"].lower()]
        if not companies:
            print(f"❌ Aucune entreprise trouvée : {args.company}")
            return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(companies)
    print(f"✉️  {total} entreprise(s) à traiter avec '{args.model}'\n")

    errors, durations = 0, []
    count_letters, count_contacts = 0, 0
    start_total = time.time()

    for company in tqdm(companies, desc="Génération", unit="entreprise"):
        nom  = company.get("nom", "inconnu")
        mode = determine_mode(company)
        start = time.time()

        try:
            if mode == "contact":
                # Pas d'offre pertinente → génère le formulaire de contact
                data     = generate_contact_form(company, args.model)
                filepath = save_contact_form(data, nom, output_dir)
                count_contacts += 1
                label = "📋 formulaire"
            else:
                # Offre(s) ou candidature spontanée → génère la lettre
                letter   = generate_letter(company, args.model)
                filepath = save_letter(letter, nom, output_dir)
                count_letters += 1
                # Indique si c'est ciblé sur une offre ou spontané
                offers = company.get("job_offers", [])
                label  = f"✉️  lettre {'ciblée' if offers else 'spontanée'}"

            duration = time.time() - start
            durations.append(duration)
            tqdm.write(f"  ✓  {nom} → {filepath.name}  [{label}]  ({format_duration(duration)})")

        except Exception as e:
            errors += 1
            duration = time.time() - start
            tqdm.write(f"  ⚠️  {nom} — Erreur : {e}  ({format_duration(duration)})")

    # ── Résumé final ────────────────────────────────────────
    total_time = time.time() - start_total
    success    = total - errors

    print(f"\n{'─' * 55}")
    print(f"✅ {success}/{total} entreprises traitées → ./{args.output}/")
    print(f"   ✉️  {count_letters} lettre(s)  |  📋 {count_contacts} formulaire(s)")
    if durations:
        avg = sum(durations) / len(durations)
        print(f"⏱  Temps total    : {format_duration(total_time)}")
        print(f"   Moyenne        : {format_duration(avg)}/entreprise")
        print(f"   Min / Max      : {format_duration(min(durations))} / {format_duration(max(durations))}")
    if errors:
        print(f"   ⚠️  {errors} erreur(s)")
    print(f"{'─' * 55}")


if __name__ == "__main__":
    main()