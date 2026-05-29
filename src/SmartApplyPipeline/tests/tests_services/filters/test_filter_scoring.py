"""Unit tests for filter scoring (prescore + deep score) and keyword detection."""

import pytest

from app.services.filters import filter_scoring as fs


# ── keyword detection ─────────────────────────────────────────

def test_detect_blacklist_found():
    assert fs.detect_blacklist("Cabinet dentaire du centre") == "dentaire"


def test_detect_blacklist_none():
    assert fs.detect_blacklist("Software development agency") == ""


def test_count_it_keywords():
    count, found = fs.count_it_keywords("We build SaaS with .NET and React")
    assert count >= 3
    assert ".net" in found and "react" in found and "saas" in found


# ── prescore ──────────────────────────────────────────────────

def test_prescore_inaccessible_is_zero():
    assert fs.compute_prescore(False, "", 5, {}) == 0


def test_prescore_blacklisted_is_one():
    assert fs.compute_prescore(True, "dentaire", 5, {}) == 1


@pytest.mark.parametrize("it_count,expected", [(0, 3), (1, 6), (2, 6), (3, 8), (10, 8)])
def test_prescore_by_keyword_count(it_count, expected):
    assert fs.compute_prescore(True, "", it_count, {}) == expected


def test_prescore_sector_bonus_capped_at_10():
    # 3+ keywords → 8, +1 IT sector bonus → 9
    assert fs.compute_prescore(True, "", 3, {"secteur": "Software house"}) == 9


# ── deep score ────────────────────────────────────────────────

def test_deep_score_full_stack():
    score = fs.compute_deep_score(
        freshness={"fresh": True},
        mx={"has_mx": True},
        careers={"has_careers": True, "it_jobs_found": True, "career_score": 3},
        prescore=6,
    )
    assert score == 10  # 6 + 3 + 1 + 1 = 11, capped at 10


def test_deep_score_no_careers_capped_at_4():
    score = fs.compute_deep_score(
        freshness={"fresh": True},
        mx={"has_mx": True},
        careers={"has_careers": False, "career_score": 0},
        prescore=8,
    )
    assert score == 4


def test_deep_score_careers_without_it_jobs_capped_at_6():
    score = fs.compute_deep_score(
        freshness={"fresh": True},
        mx={"has_mx": True},
        careers={"has_careers": True, "it_jobs_found": False, "career_score": 1},
        prescore=8,
    )
    assert score == 6
