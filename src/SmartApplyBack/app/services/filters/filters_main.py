"""
filters_main.py
---------------
Orchestre le pipeline complet de filtrage en une seule commande :
    1. prefilter   — DNS + scraping + blacklist + pré-score (sync)
    2. deep_filter — fraîcheur + MX + carrières IT (async)

Les dossiers de sortie sont créés automatiquement depuis le nom du CSV d'entrée.
Ex : entreprises_toulouse.csv → results/toulouse/

Usage :
    python filters_main.py --input ../../results/entreprises_toulouse.csv --output-dir ../../results/ 
    python filters_main.py --input entreprises_toulouse.csv --output-dir mon/dossier
    python filters_main.py --input entreprises_toulouse.csv --min-prescore 3 --min-deep-score 6
    python filters_main.py --input entreprises_toulouse.csv --skip-deep
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from filter_config  import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from filter_csv     import load_csv, save_csv, PREFILTER_FIELDS, DEEP_FILTER_FIELDS, ELIMINATED_FIELDS
from prefilter      import prefilter_companies
from deep_filter    import deep_filter_async


def build_output_dir(input_csv: str, output_dir: str | None) -> str:
    """
    Si --output-dir n'est pas fourni, génère un dossier depuis le nom du CSV.
    Ex : entreprises_toulouse.csv → results/toulouse/
         path/to/entreprises_Brussels.csv → results/brussels/
    """
    if output_dir:
        return output_dir

    base = os.path.splitext(os.path.basename(input_csv))[0]  # "entreprises_toulouse"
    city = base.split("_", 1)[-1].lower()                    # "toulouse"
    return os.path.join("results", city)


def build_paths(input_csv: str, output_dir: str) -> dict:
    """Génère tous les chemins de fichiers dans le dossier de sortie."""
    base = os.path.splitext(os.path.basename(input_csv))[0]
    return {
        "prefiltered"    : os.path.join(output_dir, f"{base}_prefiltered.csv"),
        "pre_eliminated" : os.path.join(output_dir, f"{base}_pre_eliminated.csv"),
        "deep_filtered"  : os.path.join(output_dir, f"{base}_deep_filtered.csv"),
        "deep_eliminated": os.path.join(output_dir, f"{base}_deep_eliminated.csv"),
    }


# ─── ÉTAPES ──────────────────────────────────────────────────

def run_prefilter(input_csv: str, paths: dict, min_prescore: int) -> list:
    print("\n" + "═" * 55)
    print("  🔍 ÉTAPE 1 — PRÉFILTRAGE (DNS + scraping + blacklist)")
    print("═" * 55)

    companies = load_csv(input_csv)
    if not companies:
        return []

    to_score, eliminated = prefilter_companies(companies, min_prescore)

    save_csv(
        sorted(to_score, key=lambda x: x.get("prescore", 0), reverse=True),
        paths["prefiltered"],
        PREFILTER_FIELDS,
    )
    save_csv(eliminated, paths["pre_eliminated"], ELIMINATED_FIELDS)

    print(f"\n  ✅ {len(to_score)} entreprises passent au deep filter")
    print(f"  ❌ {len(eliminated)} éliminées au préfiltrage")
    return to_score


def run_deep_filter(companies: list, paths: dict,
                    min_deep_score: int, concurrency: int) -> list:
    print("\n" + "═" * 55)
    print("  ⚡ ÉTAPE 2 — DEEP FILTER (fraîcheur + MX + carrières)")
    print("═" * 55)
    print(f"  Concurrence : {concurrency} | Score min : {min_deep_score}/10\n")

    kept, dropped = asyncio.run(
        deep_filter_async(companies, min_deep_score, concurrency)
    )

    save_csv(kept,    paths["deep_filtered"],   DEEP_FILTER_FIELDS)
    save_csv(dropped, paths["deep_eliminated"], DEEP_FILTER_FIELDS)
    return kept


def print_summary(input_csv: str, pre_kept: list, deep_kept: list,
                  paths: dict, output_dir: str, elapsed: int) -> None:
    print("\n" + "═" * 55)
    print("  📊 RÉSUMÉ FINAL")
    print("═" * 55)
    print(f"  Entrée             : {os.path.basename(input_csv)}")
    print(f"  Après préfiltrage  : {len(pre_kept)}")
    print(f"  Après deep filter  : {len(deep_kept)}")
    print(f"  Durée totale       : {elapsed}s")
    print(f"  Dossier résultats  : {output_dir}/")
    print(f"\n👉 Lance maintenant : python scorer.py --input {paths['deep_filtered']}")


# ─── POINT D'ENTRÉE ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pipeline de filtrage complet")
    parser.add_argument("--input",          required=True,                    help="CSV d'entrée (sortie du scraping)")
    parser.add_argument("--output-dir",     default=None,                     help="Dossier de sortie (auto-généré si absent)")
    parser.add_argument("--min-prescore",   type=int, default=MIN_PRESCORE,   help=f"Pré-score minimum (défaut: {MIN_PRESCORE})")
    parser.add_argument("--min-deep-score", type=int, default=MIN_DEEP_SCORE, help=f"Deep score minimum (défaut: {MIN_DEEP_SCORE})")
    parser.add_argument("--concurrency",    type=int, default=CONCURRENCY,    help=f"Workers async (défaut: {CONCURRENCY})")
    parser.add_argument("--skip-deep",      action="store_true",              help="Arrête après le préfiltrage")
    args = parser.parse_args()

    output_dir = build_output_dir(args.input, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    paths = build_paths(args.input, output_dir)
    start = datetime.now()

    print("=" * 55)
    print("  🚀 PIPELINE FILTRAGE COMPLET")
    print("=" * 55)
    print(f"  Entrée      : {args.input}")
    print(f"  Sortie      : {output_dir}/")

    # Étape 1
    pre_kept = run_prefilter(args.input, paths, args.min_prescore)
    if not pre_kept:
        print("\n⚠️  Aucune entreprise n'a passé le préfiltrage — pipeline arrêté.")
        return

    if args.skip_deep:
        print(f"\n⏭️  --skip-deep activé — pipeline arrêté après le préfiltrage.")
        print(f"👉 Résultat : {paths['prefiltered']}")
        return

    # Étape 2
    deep_kept = run_deep_filter(pre_kept, paths, args.min_deep_score, args.concurrency)

    elapsed = (datetime.now() - start).seconds
    print_summary(args.input, pre_kept, deep_kept, paths, output_dir, elapsed)


if __name__ == "__main__":
    main()
