"""
filters_main.py
---------------
Orchestre le pipeline complet de filtrage en une seule commande.
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from filter_config  import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.services.filters.filter_json import load_json, save_json, PREFILTER_FIELDS, DEEP_FILTER_FIELDS, ELIMINATED_FIELDS
from prefilter      import prefilter_companies
from deep_filter    import deep_filter_async


def build_output_dir(input_json: str, output_dir: str | None) -> str:
    if output_dir:
        return output_dir
    base = os.path.splitext(os.path.basename(input_json))[0]
    city = base.split("_", 1)[-1].lower()
    return os.path.join("results", city)


def build_paths(input_json: str, output_dir: str) -> dict:
    base = os.path.splitext(os.path.basename(input_json))[0]
    return {
        "prefiltered"    : os.path.join(output_dir, f"{base}_prefiltered.json"),
        "pre_eliminated" : os.path.join(output_dir, f"{base}_pre_eliminated.json"),
        "deep_filtered"  : os.path.join(output_dir, f"{base}_deep_filtered.json"),
        "deep_eliminated": os.path.join(output_dir, f"{base}_deep_eliminated.json"),
    }


# ─── ÉTAPES ──────────────────────────────────────────────────

def run_prefilter(input_json: str, paths: dict, min_prescore: int) -> list:
    print("\n" + "═" * 55)
    print("  🔍 ÉTAPE 1 — PRÉFILTRAGE (DNS + scraping + blacklist)")
    print("═" * 55)

    companies = load_json(input_json)
    if not companies:
        return []

    to_score, eliminated = prefilter_companies(companies, min_prescore)

    save_json(
        sorted(to_score, key=lambda x: x.get("prescore", 0), reverse=True),
        paths["prefiltered"],
        PREFILTER_FIELDS,
    )
    save_json(eliminated, paths["pre_eliminated"], ELIMINATED_FIELDS)

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

    save_json(kept,    paths["deep_filtered"],   DEEP_FILTER_FIELDS)
    save_json(dropped, paths["deep_eliminated"], DEEP_FILTER_FIELDS)
    return kept


def print_summary(input_json: str, pre_kept: list, deep_kept: list,
                  paths: dict, output_dir: str, elapsed: int) -> None:
    print("\n" + "═" * 55)
    print("  📊 RÉSUMÉ FINAL")
    print("═" * 55)
    print(f"  Entrée             : {os.path.basename(input_json)}")
    print(f"  Après préfiltrage  : {len(pre_kept)}")
    print(f"  Après deep filter  : {len(deep_kept)}")
    print(f"  Durée totale       : {elapsed}s")
    print(f"  Dossier résultats  : {output_dir}/")
    print(f"\n👉 Lance maintenant : python scorer.py --input {paths['deep_filtered']}")


# ─── POINT D'ENTRÉE ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pipeline de filtrage complet")
    parser.add_argument("--input",          required=True,                    help="JSON d'entrée (sortie du scraping)")
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

    pre_kept = run_prefilter(args.input, paths, args.min_prescore)
    if not pre_kept:
        print("\n⚠️  Aucune entreprise n'a passé le préfiltrage — pipeline arrêté.")
        return

    if args.skip_deep:
        print(f"\n⏭️  --skip-deep activé — pipeline arrêté après le préfiltrage.")
        print(f"👉 Résultat : {paths['prefiltered']}")
        return

    deep_kept = run_deep_filter(pre_kept, paths, args.min_deep_score, args.concurrency)
    elapsed   = (datetime.now() - start).seconds
    print_summary(args.input, pre_kept, deep_kept, paths, output_dir, elapsed)


if __name__ == "__main__":
    main()