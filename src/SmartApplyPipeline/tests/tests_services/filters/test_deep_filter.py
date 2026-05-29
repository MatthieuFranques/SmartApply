"""Tests for deep_filter async layers (aiohttp/aiodns mocked)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.filters import deep_filter as df


# ── check_mx_record ───────────────────────────────────────────

async def test_check_mx_record_known_provider():
    record = MagicMock()
    record.host = "aspmx.l.google.com"
    resolver = MagicMock()
    resolver.query = AsyncMock(return_value=[record])
    out = await df.check_mx_record(resolver, "acme.io")
    assert out["has_mx"] is True
    assert out["mx_provider"] == "Google Workspace"


async def test_check_mx_record_failure():
    resolver = MagicMock()
    resolver.query = AsyncMock(side_effect=Exception("no mx"))
    out = await df.check_mx_record(resolver, "ghost.io")
    assert out == {"has_mx": False, "mx_provider": ""}


# ── process_company ───────────────────────────────────────────

async def test_process_company_assembles_result():
    semaphore = asyncio.Semaphore(1)
    with patch.object(df, "check_site_freshness", new=AsyncMock(return_value={"fresh": True, "last_modified": "2025-01-01"})), \
         patch.object(df, "check_mx_record", new=AsyncMock(return_value={"has_mx": True, "mx_provider": "OVH"})), \
         patch.object(df, "check_career_page", new=AsyncMock(return_value={"has_careers": True, "it_jobs_found": True, "career_score": 3, "careers_url": "https://a/jobs"})), \
         patch.object(df.asyncio, "sleep", new=AsyncMock()):
        out = await df.process_company(
            MagicMock(), MagicMock(), semaphore,
            {"domaine": "acme.io", "nom": "Acme", "prescore": 6}, 1, 1,
        )
    assert out["deep_score"] == 10  # 6 +3 +1 +1 capped
    assert out["has_mx"] is True
    assert out["careers_url"] == "https://a/jobs"


# ── deep_filter_async ─────────────────────────────────────────

async def test_deep_filter_async_splits_kept_dropped():
    companies = [
        {"domaine": "a.io", "nom": "A"},
        {"domaine": "b.io", "nom": "B"},
    ]

    async def fake_process(session, resolver, semaphore, company, i, total):
        score = 8 if company["domaine"] == "a.io" else 2
        return {**company, "deep_score": score}

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)

    with patch.object(df.aiohttp, "TCPConnector", return_value=MagicMock()), \
         patch.object(df.aiohttp, "ClientSession", return_value=session_cm), \
         patch.object(df.aiodns, "DNSResolver", return_value=MagicMock()), \
         patch.object(df, "process_company", side_effect=fake_process):
        kept, dropped = await df.deep_filter_async(companies, min_score=5)

    assert [k["domaine"] for k in kept] == ["a.io"]
    assert [d["domaine"] for d in dropped] == ["b.io"]
