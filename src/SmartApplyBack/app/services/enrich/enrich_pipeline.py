# ============================================================
# enrich_pipeline.py
# Pipeline d'enrichissement complet par entreprise
# ============================================================

from dataclasses import asdict

from enrich_config import CompanyContext, JobOffer, ContactForm
from enrich_scraper import (
    build_url,
    fetch_page,
    scrape_page_safe,
    extract_meta_description,
    extract_main_text,
    find_about_url,
    detect_tech_keywords,
    detect_size_hint,
    detect_founded_year,
    extract_key_phrases,
    extract_job_titles,
    scrape_all_job_offers,
    scrape_contact_info,
)


def enrich_company(row: dict) -> CompanyContext:
    """
    Pipeline complet d'enrichissement pour une entreprise.

    Flux :
        1. Page principale  → description, tech, taille, phrases clés, année
        2. Page "À propos"  → enrichit le contexte et la taille
        3. Page carrières   → offres d'emploi détaillées + pertinence
             ├── Offres pertinentes trouvées → job_offers rempli
             └── Aucune offre pertinente     → scrape page contact → contact_form
    """
    ctx = CompanyContext(
        nom           = row.get("nom", ""),
        domaine       = row.get("domaine", ""),
        ville         = row.get("ville", ""),
        secteur       = row.get("secteur", ""),
        careers_url   = row.get("careers_url", ""),
        site_title    = row.get("site_title", ""),
        is_recruiting = row.get("it_jobs_found", "").lower() in ("true", "1", "yes"),
    )

    url = build_url(ctx.domaine)
    if not url:
        ctx.scrape_status = "error"
        ctx.scrape_error  = "Domaine vide"
        return ctx

    try:
        # ── 1. Page principale ──────────────────────────────
        soup = fetch_page(url)
        main_text = extract_main_text(soup)

        ctx.description       = extract_meta_description(soup)
        ctx.tech_keywords     = detect_tech_keywords(main_text)
        ctx.company_size_hint = detect_size_hint(main_text)
        ctx.key_phrases       = extract_key_phrases(main_text)
        ctx.founded_hint      = detect_founded_year(main_text)

        # ── 2. Page "À propos" ──────────────────────────────
        about_url = find_about_url(soup, url)
        if about_url:
            about_soup = scrape_page_safe(about_url)
            if about_soup:
                about_text = extract_main_text(about_soup, max_chars=2000)
                ctx.about_text    = about_text
                ctx.tech_keywords = list(set(
                    ctx.tech_keywords + detect_tech_keywords(about_text)
                ))
                if not ctx.company_size_hint:
                    ctx.company_size_hint = detect_size_hint(about_text)
                if not ctx.founded_hint:
                    ctx.founded_hint = detect_founded_year(about_text)

        # ── 3. Page carrières ───────────────────────────────
        if ctx.careers_url:
            careers_soup = scrape_page_safe(ctx.careers_url)

            if careers_soup:
                careers_text = extract_main_text(careers_soup, max_chars=3000)
                ctx.job_keywords     = list(set(detect_tech_keywords(careers_text)))
                ctx.job_titles_found = extract_job_titles(careers_text)

                if ctx.job_titles_found:
                    ctx.is_recruiting = True

                # ── 3a. Scrape des offres individuelles ─────
                offers: list[JobOffer] = scrape_all_job_offers(careers_soup, ctx.careers_url)

                if offers:
                    # Sérialise les offres en dicts pour le JSON
                    ctx.job_offers = [asdict(o) for o in offers]
                else:
                    # ── 3b. Pas d'offre pertinente → contact ─
                    contact: ContactForm = scrape_contact_info(soup, url)
                    if contact.url or contact.email_found:
                        ctx.contact_form = asdict(contact)

        # Pas de page carrières → cherche quand même le contact
        elif not ctx.careers_url:
            contact: ContactForm = scrape_contact_info(soup, url)
            if contact.url or contact.email_found:
                ctx.contact_form = asdict(contact)

        ctx.scrape_status = "ok"

    except TimeoutError as e:
        ctx.scrape_status = "timeout"
        ctx.scrape_error  = str(e)
    except Exception as e:
        ctx.scrape_status = "error"
        ctx.scrape_error  = str(e)

    return ctx


def summarize_context(ctx: CompanyContext) -> str:
    """
    Retourne un résumé lisible du résultat pour le log terminal.
    Ex: "Ntbies | 5 tech | 3 offres (max score: 8) | contact: oui"
    """
    parts = [ctx.nom]
    parts.append(f"{len(ctx.tech_keywords)} tech")

    if ctx.job_offers:
        best = max(o["relevance_score"] for o in ctx.job_offers)
        parts.append(f"{len(ctx.job_offers)} offre(s) (meilleure: {best}/10)")
    elif ctx.is_recruiting:
        parts.append("recrute mais offres non parsées")
    else:
        parts.append("pas d'offre détectée")

    if ctx.contact_form:
        has_file = ctx.contact_form.get("has_file_upload", False)
        parts.append(f"contact: oui {'(upload CV)' if has_file else ''}")

    return " | ".join(parts)