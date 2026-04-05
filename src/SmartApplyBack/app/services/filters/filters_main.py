"""
filters_main.py
---------------
Pipeline de filtrage avec streaming SSE.
"""
import asyncio
from typing import Generator

from app.services.filters.filter_config import MIN_PRESCORE, MIN_DEEP_SCORE, CONCURRENCY
from app.services.filters.prefilter     import prefilter_companies
from app.services.filters.deep_filter   import deep_filter_async


def stream_pipeline(
    jobs: list[dict],
    user_id: str,
    repo,
    min_prescore: int   = MIN_PRESCORE,
    min_deep_score: int = MIN_DEEP_SCORE,
    concurrency: int    = CONCURRENCY,
    skip_deep: bool     = False,
) -> Generator[dict, None, None]:
    """
    Générateur — yield chaque événement du pipeline de filtrage.
    """
    cities = list({job.get("ville", "") for job in jobs if job.get("ville")})
    total_pre_kept  = 0
    total_deep_kept = 0

    yield {"type": "start", "total_jobs": len(jobs), "cities": cities}

    for city in cities:
        yield {"type": "city", "city": city}

        city_jobs = [j for j in jobs if j.get("ville", "").lower() == city.lower()]

        # ── Étape 1 — Préfiltrage ─────────────────────────
        yield {"type": "step", "step": "prefilter", "city": city, "count": len(city_jobs)}

        for i, company in enumerate(city_jobs):
            yield {
                "type":    "processing",
                "step":    "prefilter",
                "company": company.get("nom", "?"),
                "domaine": company.get("domaine", ""),
                "index":   i + 1,
                "total":   len(city_jobs),
            }

        kept, eliminated = prefilter_companies(city_jobs, min_prescore)
        total_pre_kept += len(kept)

        # Mise à jour DB immédiate
        for job in kept:
            repo.update_stage(user_id, job["domaine"], stage="filtered",
                              extra_fields={"prescore": job.get("prescore")})
            yield {
                "type":     "result",
                "step":     "prefilter",
                "status":   "kept",
                "company":  job.get("nom", "?"),
                "domaine":  job.get("domaine", ""),
                "prescore": job.get("prescore"),
            }

        for job in eliminated:
            repo.update_stage(user_id, job["domaine"], stage="scraping", status="eliminated")
            yield {
                "type":    "result",
                "step":    "prefilter",
                "status":  "eliminated",
                "company": job.get("nom", "?"),
                "domaine": job.get("domaine", ""),
                "reason":  job.get("raison_filtre", ""),
            }

        if not kept or skip_deep:
            continue

        # ── Étape 2 — Deep filter ─────────────────────────
        yield {"type": "step", "step": "deep_filter", "city": city, "count": len(kept)}

        deep_kept, deep_eliminated = asyncio.run(
            deep_filter_async(kept, min_deep_score, concurrency)
        )
        total_deep_kept += len(deep_kept)

        for job in deep_kept:
            repo.update_stage(user_id, job["domaine"], stage="deep",
                              extra_fields={"deep_score": job.get("deep_score")})
            yield {
                "type":       "result",
                "step":       "deep_filter",
                "status":     "kept",
                "company":    job.get("nom", "?"),
                "domaine":    job.get("domaine", ""),
                "deep_score": job.get("deep_score"),
            }

        for job in deep_eliminated:
            repo.update_stage(user_id, job["domaine"], stage="filtered", status="eliminated")
            yield {
                "type":       "result",
                "step":       "deep_filter",
                "status":     "eliminated",
                "company":    job.get("nom", "?"),
                "domaine":    job.get("domaine", ""),
                "deep_score": job.get("deep_score"),
            }

    yield {
        "type":           "done",
        "total_pre_kept": total_pre_kept,
        "total_deep_kept": total_deep_kept,
    }