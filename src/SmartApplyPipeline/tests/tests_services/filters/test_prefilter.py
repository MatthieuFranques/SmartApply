"""Tests for prefilter (DNS check, site fetch, scoring pipeline) — network mocked."""

import socket
from unittest.mock import MagicMock, patch

from app.services.filters import prefilter as pf


def test_check_domain_dns_ok():
    with patch.object(pf.socket, "gethostbyname", return_value="1.2.3.4"):
        assert pf.check_domain_dns("acme.io") is True


def test_check_domain_dns_fail():
    with patch.object(pf.socket, "gethostbyname", side_effect=socket.gaierror):
        assert pf.check_domain_dns("ghost.io") is False


def test_fetch_site_content_success():
    html = '<html><head><title>Acme</title><meta name="description" content="best">' \
           '<meta name="keywords" content="python"></head></html>'
    resp = MagicMock()
    resp.status_code = 200
    resp.text = html
    with patch.object(pf.requests, "get", return_value=resp):
        out = pf.fetch_site_content("acme.io")
    assert out["accessible"] is True
    assert out["title"] == "Acme"
    assert out["description"] == "best"
    assert out["keywords"] == "python"


def test_fetch_site_content_inaccessible():
    with patch.object(pf.requests, "get", side_effect=Exception("boom")):
        out = pf.fetch_site_content("ghost.io")
    assert out["accessible"] is False


def test_prefilter_companies_classification():
    companies = [
        {"nom": "Good", "domaine": "good.io", "secteur": "IT"},
        {"nom": "DeadDNS", "domaine": "dead.io", "secteur": ""},
        {"nom": "Down", "domaine": "down.io", "secteur": ""},
        {"nom": "Blacklisted", "domaine": "dental.io", "secteur": ""},
    ]

    def fake_dns(domain):
        return domain != "dead.io"

    def fake_content(domain):
        if domain == "down.io":
            return {"accessible": False, "title": "", "description": "", "keywords": ""}
        if domain == "dental.io":
            return {"accessible": True, "title": "Cabinet dentaire", "description": "", "keywords": ""}
        # good.io
        return {"accessible": True, "title": "Software dev .NET react",
                "description": "python api cloud", "keywords": "devops"}

    with patch.object(pf, "check_domain_dns", side_effect=fake_dns), \
         patch.object(pf, "fetch_site_content", side_effect=fake_content), \
         patch.object(pf.time, "sleep"):
        kept, eliminated = pf.prefilter_companies(companies, min_prescore=4)

    assert [k["nom"] for k in kept] == ["Good"]
    reasons = {e["nom"]: e.get("raison_filtre") for e in eliminated}
    assert reasons["DeadDNS"] == "DNS invalide"
    assert reasons["Down"] == "Site inaccessible"
    assert reasons["Blacklisted"] == "dentaire"
