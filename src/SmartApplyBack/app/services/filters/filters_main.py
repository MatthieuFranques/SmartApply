"""
filters_main.py
---------------
Orchestre le pipeline complet de filtrage en une seule commande.
"""

import os
import asyncio
from datetime import datetime

from app.services.filters.filter_config  import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.services.filters.filter_json    import load_json, save_json, PREFILTER_FIELDS, DEEP_FILTER_FIELDS, ELIMINATED_FIELDS
from app.services.filters.prefilter      import prefilter_companies
from app.services.filters.deep_filter    import deep_filter_async


# ─── Chemins ─────────────────────────────────────────────────

def get_input_path(base_dir: str = "results") -> str:
    return os.path.join(base_dir, "scraping_results.json")

def build_paths(base_dir: str = "results") -> dict:
    return {
        "prefiltered"    : os.path.join(base_dir, "filter_results.json"),
        "pre_eliminated" : os.path.join(base_dir, "filter_eliminated.json"),
        "deep_filtered"  : os.path.join(base_dir, "deep_results.json"),
        "deep_eliminated": os.path.join(base_dir, "deep_eliminated.json"),
    }


# ─── ÉTAPES ──────────────────────────────────────────────────

def run_prefilter(city: str, paths: dict, min_prescore: int, base_dir: str = "results") -> list:
    print("\n" + "═" * 55)
    print("  🔍 ÉTAPE 1 — PRÉFILTRAGE (DNS + scraping + blacklist)")
    print("═" * 55)

    input_file = get_input_path(base_dir)
    print(f"  📂 Fichier : {input_file} | Existe : {os.path.exists(input_file)}")

    if not os.path.exists(input_file):
        print(f"  ❌ Fichier introuvable : {input_file}")
        return []

    all_companies = load_json(input_file)
    companies     = [c for c in all_companies if c.get("ville", "").lower() == city.lower()]
    print(f"  📋 {len(companies)} entreprises pour {city} (sur {len(all_companies)} total)")

    if not companies:
        return []

    to_score, eliminated = prefilter_companies(companies, min_prescore)

    # ── Merge sans doublons ───────────────────────────────────
    existing_pre  = load_json(paths["prefiltered"])    if os.path.exists(paths["prefiltered"])    else []
    existing_elim = load_json(paths["pre_eliminated"]) if os.path.exists(paths["pre_eliminated"]) else []
    existing_domains = {c["domaine"] for c in existing_pre + existing_elim}

    merged_pre  = existing_pre  + [c for c in to_score   if c["domaine"] not in existing_domains]
    merged_elim = existing_elim + [c for c in eliminated if c["domaine"] not in existing_domains]

    save_json(sorted(merged_pre, key=lambda x: x.get("prescore", 0), reverse=True),
              paths["prefiltered"], PREFILTER_FIELDS)
    save_json(merged_elim, paths["pre_eliminated"], ELIMINATED_FIELDS)

    print(f"\n  ✅ {len(to_score)} passent | ❌ {len(eliminated)} éliminées")
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

    # ── Merge sans doublons ───────────────────────────────────
    existing_kept    = load_json(paths["deep_filtered"])   if os.path.exists(paths["deep_filtered"])   else []
    existing_dropped = load_json(paths["deep_eliminated"]) if os.path.exists(paths["deep_eliminated"]) else []
    existing_domains = {c["domaine"] for c in existing_kept + existing_dropped}

    merged_kept    = existing_kept    + [c for c in kept    if c["domaine"] not in existing_domains]
    merged_dropped = existing_dropped + [c for c in dropped if c["domaine"] not in existing_domains]

    save_json(sorted(merged_kept, key=lambda x: x["deep_score"], reverse=True),
              paths["deep_filtered"], DEEP_FILTER_FIELDS)
    save_json(merged_dropped, paths["deep_eliminated"], DEEP_FILTER_FIELDS)

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

    os.makedirs(base_dir, exist_ok=True)
    paths = build_paths(base_dir)  # ← fichiers plats, pas de sous-dossiers

    all_pre_kept  = []
    all_deep_kept = []

    for city in cities:
        print(f"\n{'═'*55}")
        print(f"  🌍 Ville : {city}")
        print(f"{'═'*55}")

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
        "paths"    : paths,
    }


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline de filtrage complet")
    parser.add_argument("--cities",         nargs="+", default=["Toulouse", "Brussels", "Namur"])
    parser.add_argument("--base-dir",       default="results")
    parser.add_argument("--min-prescore",   type=int, default=MIN_PRESCORE)
    parser.add_argument("--min-deep-score", type=int, default=MIN_DEEP_SCORE)
    parser.add_argument("--concurrency",    type=int, default=CONCURRENCY)
    parser.add_argument("--skip-deep",      action="store_true")
    args = parser.parse_args()

    start  = datetime.now()
    result = run_pipeline(
        cities         = args.cities,
        base_dir       = args.base_dir,
        min_prescore   = args.min_prescore,
        min_deep_score = args.min_deep_score,
        concurrency    = args.concurrency,
        skip_deep      = args.skip_deep,
    )
    elapsed = (datetime.now() - start).seconds
    print_summary(args.cities, result["pre_kept"], result["deep_kept"], args.base_dir, elapsed)
