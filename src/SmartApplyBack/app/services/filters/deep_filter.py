"""
deep_filter.py
--------------
Filtrage approfondi ASYNC — 3 couches gratuites.
"""

import os
import sys
import asyncio
import argparse
import aiohttp
import aiodns

sys.path.insert(0, os.path.dirname(__file__))

from bs4           import BeautifulSoup
from datetime      import datetime, timezone
from dotenv        import load_dotenv
from email.utils   import parsedate_to_datetime
from filter_config import (TIMEOUT_HTTP, PAUSE, CONCURRENCY, MIN_DEEP_SCORE,
                            HTTP_HEADERS, CAREER_PATHS, MX_PROVIDERS, IT_KEYWORDS)
from app.services.filters.filter_json import load_json, save_json, DEEP_FILTER_FIELDS
from filter_scoring import compute_deep_score

load_dotenv()

DEFAULT_INPUT  = "entreprises_prefiltered.json"
DEFAULT_OUTPUT = "entreprises_deep_filtered.json"


# ─── COUCHE 1 — FRAÎCHEUR DU SITE ───────────────────────────

async def check_site_freshness(session: aiohttp.ClientSession, domain: str) -> dict:
    for scheme in ["https://", "http://"]:
        try:
            async with session.get(
                f"{scheme}{domain}",
                headers         = HTTP_HEADERS,
                allow_redirects = True,
                timeout         = aiohttp.ClientTimeout(total=TIMEOUT_HTTP),
            ) as response:
                if response.status != 200:
                    continue

                text          = await response.text(errors="replace")
                score         = 0
                last_modified = ""
                current_year  = datetime.now().year

                lm_header = response.headers.get("Last-Modified", "")
                if lm_header:
                    try:
                        lm_date       = parsedate_to_datetime(lm_header)
                        age_days      = (datetime.now(timezone.utc) - lm_date).days
                        last_modified = lm_date.strftime("%Y-%m-%d")
                        score        += 2 if age_days < 180 else (1 if age_days < 365 else 0)
                    except Exception:
                        pass

                soup = BeautifulSoup(text, "html.parser")
                body = soup.get_text()

                if str(current_year) in body:
                    score += 2
                elif str(current_year - 1) in body:
                    score += 1

                for tag in soup.find_all("time"):
                    dt = tag.get("datetime", "")
                    if str(current_year) in dt or str(current_year - 1) in dt:
                        score += 1
                        break

                return {
                    "fresh"          : score >= 2,
                    "last_modified"  : last_modified,
                    "freshness_score": min(score, 3),
                }
        except Exception:
            continue

    return {"fresh": False, "last_modified": "", "freshness_score": 0}


# ─── COUCHE 2 — VÉRIFICATION MX ─────────────────────────────

async def check_mx_record(resolver: aiodns.DNSResolver, domain: str) -> dict:
    try:
        mx_records = await resolver.query(domain, "MX")
        if not mx_records:
            return {"has_mx": False, "mx_provider": ""}

        mx_host     = str(mx_records[0].host).lower()
        mx_provider = next(
            (label for key, label in MX_PROVIDERS.items() if key in mx_host),
            "autre"
        )
        return {"has_mx": True, "mx_provider": mx_provider}

    except Exception:
        return {"has_mx": False, "mx_provider": ""}


# ─── COUCHE 3 — PAGE CARRIÈRES ───────────────────────────────

async def check_career_page(session: aiohttp.ClientSession, domain: str) -> dict:
    empty = {"has_careers": False, "careers_url": "", "it_jobs_found": False, "career_score": 0}

    async def try_path(scheme: str, path: str) -> dict | None:
        try:
            async with session.get(
                f"{scheme}{domain}{path}",
                headers         = HTTP_HEADERS,
                allow_redirects = True,
                timeout         = aiohttp.ClientTimeout(total=TIMEOUT_HTTP),
            ) as response:
                if response.status != 200:
                    return None
                html          = await response.text(errors="replace")
                text          = BeautifulSoup(html, "html.parser").get_text().lower()
                it_jobs_found = any(kw in text for kw in IT_KEYWORDS)
                return {
                    "has_careers"  : True,
                    "careers_url"  : f"{scheme}{domain}{path}",
                    "it_jobs_found": it_jobs_found,
                    "career_score" : 3 if it_jobs_found else 1,
                }
        except Exception:
            return None

    results = await asyncio.gather(*[
        try_path(scheme, path)
        for scheme in ["https://", "http://"]
        for path in CAREER_PATHS
    ])

    best = None
    for r in results:
        if r and (best is None or r["career_score"] > best["career_score"]):
            best = r

    return best if best else empty


# ─── TRAITEMENT D'UNE ENTREPRISE ─────────────────────────────

async def process_company(session: aiohttp.ClientSession,
                           resolver: aiodns.DNSResolver,
                           semaphore: asyncio.Semaphore,
                           company: dict,
                           index: int, total: int) -> dict:
    async with semaphore:
        domain = company.get("domaine", "")
        name   = company.get("nom", "?")
        print(f"  [{index}/{total}] 🔍 {name} ({domain})")

        freshness, mx, careers = await asyncio.gather(
            check_site_freshness(session, domain),
            check_mx_record(resolver, domain),
            check_career_page(session, domain),
        )

        prescore   = int(company.get("prescore", 3))
        deep_score = compute_deep_score(freshness, mx, careers, prescore)

        print(f"           → {deep_score}/10 | "
              f"Frais:{freshness['fresh']} | "
              f"MX:{mx['has_mx']} | "
              f"Carrières:{careers['has_careers']}")

        await asyncio.sleep(PAUSE)

        return {
            **company,
            "deep_score"   : deep_score,
            "fresh"        : freshness.get("fresh"),
            "last_modified": freshness.get("last_modified"),
            "has_mx"       : mx.get("has_mx"),
            "mx_provider"  : mx.get("mx_provider"),
            "has_careers"  : careers.get("has_careers"),
            "it_jobs_found": careers.get("it_jobs_found"),
            "careers_url"  : careers.get("careers_url"),
        }


# ─── PIPELINE PRINCIPAL ──────────────────────────────────────

async def deep_filter_async(companies: list,
                             min_score: int = MIN_DEEP_SCORE,
                             concurrency: int = CONCURRENCY) -> tuple:
    semaphore = asyncio.Semaphore(concurrency)
    total     = len(companies)

    connector = aiohttp.TCPConnector(
        limit          = concurrency * 4,
        limit_per_host = 3,
        ttl_dns_cache  = 300,
        ssl            = False,
    )

    async with aiohttp.ClientSession(connector=connector, headers=HTTP_HEADERS) as session:
        resolver = aiodns.DNSResolver()
        results  = await asyncio.gather(*[
            process_company(session, resolver, semaphore, company, i + 1, total)
            for i, company in enumerate(companies)
        ])

    kept    = sorted(
        [r for r in results if r["deep_score"] >= min_score],
        key=lambda x: x["deep_score"], reverse=True,
    )
    dropped = [r for r in results if r["deep_score"] < min_score]
    return kept, dropped