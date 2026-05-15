"""
indeed_rss.py
-------------
Scrape public Indeed RSS feed.
No API key required. Legal public endpoint.
"""

import hashlib
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}
_BASE_URL = "https://fr.indeed.com/rss"

# Indeed XML namespace
_NS = "https://www.indeed.com/"


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()[:600]


def _parse_date(date_str: str) -> str:
    try:
        return parsedate_to_datetime(date_str).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _parse_item(item: ET.Element) -> dict:
    def text(tag: str) -> str:
        el = item.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    def nstext(tag: str) -> str:
        el = item.find(f"{{{_NS}}}{tag}")
        return el.text.strip() if el is not None and el.text else ""

    url   = text("link")
    title = text("title")

    # Indeed RSS title format: "Job Title - Company" — split on " - "
    company = nstext("company")
    if not company and " - " in title:
        parts   = title.rsplit(" - ", 1)
        title   = parts[0].strip()
        company = parts[1].strip()

    return {
        "id":            hashlib.md5(url.encode()).hexdigest(),
        "title":         title,
        "company":       company or nstext("org"),
        "location":      nstext("city") or nstext("state") or "",
        "url":           url,
        "description":   _clean_html(text("description")),
        "date_posted":   _parse_date(text("pubDate")),
        "source":        "indeed",
        "status":        "new",
        "relevance_score": None,
        "tech_required": [],
    }


def search_indeed(
    keywords:    str,
    location:    str = "France",
    days:        int = 30,
    max_results: int = 50,
) -> list[dict]:
    """
    Fetch job offers from Indeed public RSS.

    Args:
        keywords:    search query (e.g. "développeur .NET fullstack")
        location:    city or country
        days:        only posts from the last N days
        max_results: cap results
    """
    params = {
        "q":      keywords,
        "l":      location,
        "sort":   "date",
        "radius": "50",
        "fromage": str(days),
    }

    try:
        resp = requests.get(_BASE_URL, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Indeed RSS] {e}")
        return []

    try:
        root    = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []
        items = [_parse_item(item) for item in channel.findall("item")]
        return items[:max_results]
    except ET.ParseError as e:
        print(f"[Indeed RSS] XML parse error: {e}")
        return []
