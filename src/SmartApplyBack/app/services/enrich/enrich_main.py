"""
enrich_main.py
--------------
Enrichissement avec streaming SSE.
"""
import time
from dataclasses import asdict
from typing import Generator

from app.services.enrich.enrich_pipeline import enrich_company, summarize_context


def stream_enrich(
    jobs: list[dict],
    user_id: str,
    repo,
    limit: int = None,
) -> Generator[dict, None, None]:
    """
    Générateur — yield chaque entreprise enrichie au fur et à mesure.
    """
    if limit:
        jobs = jobs[:limit]

    total  = len(jobs)
    errors = 0

    yield {"type": "start", "total": total}

    for i, row in enumerate(jobs, 1):
        yield {
            "type":    "processing",
            "company": row.get("nom", "?"),
            "domaine": row.get("domaine", ""),
            "index":   i,
            "total":   total,
        }

        try:
            ctx     = enrich_company(row)
            enriched = asdict(ctx)
            enriched["domaine"] = row["domaine"]
            enriched["user_id"] = row.get("user_id", "")

            # Sauvegarde immédiate en DB
            repo.update_stage(
                user_id      = user_id,
                domaine      = row["domaine"],
                stage        = "enriched",
                extra_fields = {
                    "description":       enriched.get("description"),
                    "about_text":        enriched.get("about_text"),
                    "tech_keywords":     enriched.get("tech_keywords", []),
                    "job_keywords":      enriched.get("job_keywords", []),
                    "job_titles_found":  enriched.get("job_titles_found", []),
                    "key_phrases":       enriched.get("key_phrases", []),
                    "company_size_hint": enriched.get("company_size_hint"),
                    "is_recruiting":     enriched.get("is_recruiting"),
                    "job_offers":        enriched.get("job_offers", []),
                    "contact_form":      enriched.get("contact_form"),
                    "scrape_status":     enriched.get("scrape_status"),
                    "scrape_error":      enriched.get("scrape_error"),
                },
            )

            if ctx.scrape_status != "ok":
                errors += 1
                yield {
                    "type":    "result",
                    "status":  "error",
                    "company": row.get("nom", "?"),
                    "domaine": row.get("domaine", ""),
                    "error":   ctx.scrape_error,
                }
            else:
                yield {
                    "type":         "result",
                    "status":       "ok",
                    "company":      row.get("nom", "?"),
                    "domaine":      row.get("domaine", ""),
                    "summary":      summarize_context(ctx),
                    "is_recruiting": ctx.is_recruiting,
                    "job_offers":   len(ctx.job_offers),
                    "has_contact":  bool(ctx.contact_form),
                }

        except Exception as e:
            errors += 1
            yield {
                "type":    "result",
                "status":  "error",
                "company": row.get("nom", "?"),
                "domaine": row.get("domaine", ""),
                "error":   str(e),
            }

        time.sleep(1.5)

    yield {
        "type":    "done",
        "total":   total,
        "success": total - errors,
        "errors":  errors,
    }