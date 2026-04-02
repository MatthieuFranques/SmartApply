"""
filters_main.py
---------------
Orchestre le pipeline complet de filtrage en une seule commande.
Plus de fichiers JSON — les données viennent de la DB et y retournent via le router.
"""

import asyncio
from datetime import datetime

from app.services.filters.filter_config import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.services.filters.prefilter     import prefilter_companies
from app.services.filters.deep_filter   import deep_filter_async


# ─── ÉTAPES ──────────────────────────────────────────────────

def run_prefilter(
    companies: list[dict],
    city: str,
    min_prescore: int,
) -> tuple[list[dict], list[dict]]:
    """
    Étape 1 — Préfiltrage.
    Reçoit les entreprises depuis la DB (plus de lecture fichier).
    Retourne (kept, eliminated) — c'est le router qui met à jour la DB.
    """
    print("\n" + "═" * 55)
    print("  🔍 ÉTAPE 1 — PRÉFILTRAGE (DNS + scraping + blacklist)")
    print("═" * 55)

    city_companies = [c for c in companies if c.get("ville", "").lower() == city.lower()]
    print(f"  📋 {len(city_companies)} entreprises pour {city} (sur {len(companies)} total)")

    if not city_companies:
        return [], []

    kept, eliminated = prefilter_companies(city_companies, min_prescore)

    print(f"\n  ✅ {len(kept)} passent | ❌ {len(eliminated)} éliminées")
    return kept, eliminated


def run_deep_filter(
    companies: list[dict],
    min_deep_score: int,
    concurrency: int,
) -> tuple[list[dict], list[dict]]:
    """
    Étape 2 — Deep filter.
    Reçoit les entreprises pré-filtrées.
    Retourne (kept, eliminated) — c'est le router qui met à jour la DB.
    """
    print("\n" + "═" * 55)
    print("  ⚡ ÉTAPE 2 — DEEP FILTER (fraîcheur + MX + carrières)")
    print("═" * 55)
    print(f"  Concurrence : {concurrency} | Score min : {min_deep_score}/10\n")

    kept, eliminated = asyncio.run(
        deep_filter_async(companies, min_deep_score, concurrency)
    )

    print(f"\n  ✅ {len(kept)} passent | ❌ {len(eliminated)} éliminées")
    return kept, eliminated


def print_summary(
    cities: list[str],
    pre_kept: list[dict],
    deep_kept: list[dict],
    elapsed: int,
) -> None:
    print("\n" + "═" * 55)
    print("  📊 RÉSUMÉ FINAL")
    print("═" * 55)
    print(f"  Villes             : {', '.join(cities)}")
    print(f"  Après préfiltrage  : {len(pre_kept)}")
    print(f"  Après deep filter  : {len(deep_kept)}")
    print(f"  Durée totale       : {elapsed}s")


# ─── PIPELINE PRINCIPAL ──────────────────────────────────────

def run_pipeline(
    jobs: list[dict],                       # ← vient de la DB via le router
    min_prescore: int   = MIN_PRESCORE,
    min_deep_score: int = MIN_DEEP_SCORE,
    concurrency: int    = CONCURRENCY,
    skip_deep: bool     = False,
) -> dict:
    """
    Reçoit les jobs depuis la DB, retourne les résultats catégorisés.
    Plus de base_dir, cities, ni chemins de fichiers.
    Le router se charge de mettre à jour la DB avec les résultats.
    """
    all_pre_kept      : list[dict] = []
    all_pre_eliminated: list[dict] = []
    all_deep_kept     : list[dict] = []
    all_deep_eliminated: list[dict] = []

    # Récupère les villes uniques depuis les jobs
    cities = list({job.get("ville", "") for job in jobs if job.get("ville")})

    for city in cities:
        print(f"\n{'═'*55}")
        print(f"  🌍 Ville : {city}")
        print(f"{'═'*55}")

        pre_kept, pre_eliminated = run_prefilter(jobs, city, min_prescore)

        all_pre_kept.extend(pre_kept)
        all_pre_eliminated.extend(pre_eliminated)

        if not pre_kept:
            print(f"\n⚠️  Aucune entreprise pour {city} — ville ignorée.")
            continue

        if skip_deep:
            print(f"\n⏭️  --skip-deep activé pour {city}.")
            continue

        deep_kept, deep_eliminated = run_deep_filter(pre_kept, min_deep_score, concurrency)

        all_deep_kept.extend(deep_kept)
        all_deep_eliminated.extend(deep_eliminated)

    return {
        "pre_kept"       : all_pre_kept,        # → stage "filtered"
        "pre_eliminated" : all_pre_eliminated,  # → stage "scraping" + status "eliminated"
        "deep_kept"      : all_deep_kept,        # → stage "deep"
        "deep_eliminated": all_deep_eliminated,  # → stage "filtered" + status "eliminated"
    }


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from app.repositories.job_repository import JobRepository

    parser = argparse.ArgumentParser(description="Pipeline de filtrage complet")
    parser.add_argument("--user-id",        required=True)
    parser.add_argument("--min-prescore",   type=int, default=MIN_PRESCORE)
    parser.add_argument("--min-deep-score", type=int, default=MIN_DEEP_SCORE)
    parser.add_argument("--concurrency",    type=int, default=CONCURRENCY)
    parser.add_argument("--skip-deep",      action="store_true")
    args = parser.parse_args()

    repo = JobRepository()
    jobs = [job.model_dump() for job in repo.find_by_stage(args.user_id, stage="scraping")]

    start  = datetime.now()
    result = run_pipeline(
        jobs           = jobs,
        min_prescore   = args.min_prescore,
        min_deep_score = args.min_deep_score,
        concurrency    = args.concurrency,
        skip_deep      = args.skip_deep,
    )
    elapsed = (datetime.now() - start).seconds

    # Mise à jour DB depuis le CLI
    for job in result["pre_kept"]:
        repo.update_stage(args.user_id, job["domaine"], stage="filtered",
                          extra_fields={"prescore": job.get("prescore")})
    for job in result["pre_eliminated"]:
        repo.update_stage(args.user_id, job["domaine"], stage="scraping", status="eliminated")
    for job in result["deep_kept"]:
        repo.update_stage(args.user_id, job["domaine"], stage="deep",
                          extra_fields={"deep_score": job.get("deep_score")})
    for job in result["deep_eliminated"]:
        repo.update_stage(args.user_id, job["domaine"], stage="filtered", status="eliminated")

    cities = list({job.get("ville", "") for job in jobs})
    print_summary(cities, result["pre_kept"], result["deep_kept"], elapsed)