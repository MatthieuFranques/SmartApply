"""
enrich_main.py
--------------
Logique métier partagée entre le router FastAPI et le CLI.
Plus de fichiers JSON — les données viennent de la DB et y retournent via le router.
"""

import time
from dataclasses import asdict

from app.models.enrich import EnrichSummary
from app.services.enrich.enrich_pipeline import enrich_company, summarize_context


# ─── Pipeline d'enrichissement ───────────────────────────────

def run_enrich(jobs: list[dict], limit: int = None) -> list[dict]:
    """
    Reçoit les jobs depuis la DB (plus de lecture fichier).
    Retourne la liste des jobs enrichis — c'est le router qui met à jour la DB.
    """
    print(f"\n{'═'*55}")
    print(f"  🧬 ENRICHISSEMENT")
    print(f"{'═'*55}")

    if limit:
        jobs = jobs[:limit]

    print(f"  📋 {len(jobs)} entreprise(s) à traiter\n")

    results, errors = [], 0
    total = len(jobs)

    for i, row in enumerate(jobs, 1):
        print(f"  [{i}/{total}] 🔍 {row.get('nom', '?')} ({row.get('domaine', '?')})")

        ctx = enrich_company(row)
        enriched = asdict(ctx)

        # On réinjecte les champs d'origine pour que le router
        # puisse faire l'upsert sur domaine + user_id
        enriched["domaine"]  = row["domaine"]
        enriched["user_id"]  = row.get("user_id", "")

        results.append(enriched)

        if ctx.scrape_status != "ok":
            errors += 1
            print(f"      ⚠️  {ctx.scrape_status} : {ctx.scrape_error}")
        else:
            print(f"      ✅ {summarize_context(ctx)}")

        time.sleep(1.5)

    # ─── Résumé console ──────────────────────────────────────
    print(f"\n  📊 RÉSUMÉ")
    print(f"  Total    : {len(results)}")
    print(f"  Succès   : {len(results) - errors}")
    print(f"  Erreurs  : {errors}")
    print(f"  Offres   : {sum(1 for r in results if r.get('job_offers'))}")
    print(f"  Contacts : {sum(1 for r in results if r.get('contact_form'))}")

    return results  # ← le router se charge de la DB


def build_enrich_summary(results: list[dict], errors: int) -> EnrichSummary:
    """
    Construit le résumé retourné par la route POST /enrich/start.
    Séparé de run_enrich pour pouvoir être testé indépendamment.
    """
    return EnrichSummary(
        total        = len(results),
        success      = len(results) - errors,
        errors       = errors,
        with_offers  = sum(1 for r in results if r.get("job_offers")),
        with_contact = sum(1 for r in results if r.get("contact_form")),
    )


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from app.repositories.job_repository import JobRepository

    parser = argparse.ArgumentParser(description="Enrichit les entreprises via scraping.")
    parser.add_argument("--user-id", required=True, help="google_id de l'utilisateur")
    parser.add_argument("--limit",   type=int,      help="Nombre max d'entreprises")
    args = parser.parse_args()

    repo = JobRepository()
    jobs = [job.model_dump() for job in repo.find_by_stage(args.user_id, stage="deep")]

    if not jobs:
        print("  ❌ Aucun job au stage 'deep' — lancez d'abord le filter.")
        exit(1)

    results = run_enrich(jobs, args.limit)

    # Mise à jour DB depuis le CLI
    errors = 0
    for job in results:
        if job.get("scrape_status") != "ok":
            errors += 1
        repo.update_stage(
            user_id      = args.user_id,
            domaine      = job["domaine"],
            stage        = "enriched",
            extra_fields = {
                "description":       job.get("description"),
                "about_text":        job.get("about_text"),
                "tech_keywords":     job.get("tech_keywords", []),
                "job_keywords":      job.get("job_keywords", []),
                "job_titles_found":  job.get("job_titles_found", []),
                "key_phrases":       job.get("key_phrases", []),
                "company_size_hint": job.get("company_size_hint"),
                "is_recruiting":     job.get("is_recruiting"),
                "job_offers":        job.get("job_offers", []),
                "contact_form":      job.get("contact_form"),
                "scrape_status":     job.get("scrape_status"),
                "scrape_error":      job.get("scrape_error"),
            },
        )

    summary = build_enrich_summary(results, errors)
    print(f"\n  💾 {summary.success}/{summary.total} entreprises sauvegardées en DB")