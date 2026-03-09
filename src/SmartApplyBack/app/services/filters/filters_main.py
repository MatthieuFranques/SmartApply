"""
filters_main.py
---------------
Orchestre le pipeline complet de filtrage en une seule commande.
"""

import os
import asyncio
import argparse
from datetime import datetime

from app.services.filters.filter_config  import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.services.filters.filter_json    import load_json, save_json, PREFILTER_FIELDS, DEEP_FILTER_FIELDS, ELIMINATED_FIELDS
from app.services.filters.prefilter      import prefilter_companies
from app.services.filters.deep_filter    import deep_filter_async


# ─── Chemins ─────────────────────────────────────────────────

def get_input_path(city: str, base_dir: str = "results") -> str:
    """Retourne le chemin du fichier scraping pour une ville."""
    return os.path.join(base_dir, f"scraping_results_{city.lower()}.json")


def build_output_dir(city: str, base_dir: str = "results") -> str:
    """Génère le dossier de sortie depuis le nom de la ville."""
    return os.path.join(base_dir, city.lower())


def build_paths(city: str, output_dir: str) -> dict:
    return {
        "prefiltered"    : os.path.join(output_dir, f"filter_results_{city.lower()}.json"),
        "pre_eliminated" : os.path.join(output_dir, f"filter_eliminated_{city.lower()}.json"),
        "deep_filtered"  : os.path.join(output_dir, f"deep_results_{city.lower()}.json"),
        "deep_eliminated": os.path.join(output_dir, f"deep_eliminated_{city.lower()}.json"),
    }


# ─── ÉTAPES ──────────────────────────────────────────────────

def run_prefilter(city: str, paths: dict, min_prescore: int, base_dir: str = "results") -> list:
    print("\n" + "═" * 55)
    print("  🔍 ÉTAPE 1 — PRÉFILTRAGE (DNS + scraping + blacklist)")
    print("═" * 55)

    input_file = get_input_path(city, base_dir)

    if not os.path.exists(input_file):
        print(f"⚠️  Fichier introuvable : {input_file}")
        return []

    companies = load_json(input_file)
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


def print_summary(cities: list, pre_kept: list, deep_kept: list,
                  base_dir: str, elapsed: int) -> None:
    print("\n" + "═" * 55)
    print("  📊 RÉSUMÉ FINAL")
    print("═" * 55)
    print(f"  Villes             : {', '.join(cities)}")
    print(f"  Après préfiltrage  : {len(pre_kept)}")
    print(f"  Après deep filter  : {len(deep_kept)}")
    print(f"  Durée totale       : {elapsed}s")
    print(f"  Dossier résultats  : {base_dir}/")


# ─── PIPELINE PRINCIPAL ──────────────────────────────────────

def run_pipeline(cities: list, base_dir: str = "results", min_prescore: int = MIN_PRESCORE,
                 min_deep_score: int = MIN_DEEP_SCORE, concurrency: int = CONCURRENCY,
                 skip_deep: bool = False) -> dict:
    """
    Lance le pipeline complet pour une ou plusieurs villes.
    Appelable par le router FastAPI ou en ligne de commande.
    """
    all_pre_kept  = []
    all_deep_kept = []
    all_paths     = {}

    for city in cities:
        print(f"\n{'═'*55}")
        print(f"  🌍 Ville : {city}")
        print(f"{'═'*55}")

        output_dir = build_output_dir(city, base_dir)
        os.makedirs(output_dir, exist_ok=True)
        paths = build_paths(city, output_dir)
        all_paths[city] = paths

        pre_kept = run_prefilter(city, paths, min_prescore, base_dir)
        if not pre_kept:
            print(f"\n⚠️  Aucune entreprise pour {city} — ville ignorée.")
            continue

        all_pre_kept.extend(pre_kept)

        if skip_deep:
            print(f"\n⏭️  --skip-deep activé pour {city}.")
            continue

        deep_kept = run_deep_filter(pre_kept, paths, min_deep_score, concurrency)
        all_deep_kept.extend(deep_kept)

    return {
        "pre_kept" : all_pre_kept,
        "deep_kept": all_deep_kept,
        "paths"    : all_paths,
    }


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de filtrage complet")
    parser.add_argument("--cities",         nargs="+", default=["Toulouse", "Brussels", "Namur"], help="Villes à filtrer")
    parser.add_argument("--base-dir",       default="results",        help="Dossier de base contenant les fichiers scraping")
    parser.add_argument("--min-prescore",   type=int, default=MIN_PRESCORE,   help=f"Pré-score minimum (défaut: {MIN_PRESCORE})")
    parser.add_argument("--min-deep-score", type=int, default=MIN_DEEP_SCORE, help=f"Deep score minimum (défaut: {MIN_DEEP_SCORE})")
    parser.add_argument("--concurrency",    type=int, default=CONCURRENCY,    help=f"Workers async (défaut: {CONCURRENCY})")
    parser.add_argument("--skip-deep",      action="store_true",              help="Arrête après le préfiltrage")
    args = parser.parse_args()

    start  = datetime.now()
    result = run_pipeline(
        cities        = args.cities,
        base_dir      = args.base_dir,
        min_prescore  = args.min_prescore,
        min_deep_score= args.min_deep_score,
        concurrency   = args.concurrency,
        skip_deep     = args.skip_deep,
    )
    elapsed = (datetime.now() - start).seconds
    print_summary(args.cities, result["pre_kept"], result["deep_kept"], args.base_dir, elapsed)