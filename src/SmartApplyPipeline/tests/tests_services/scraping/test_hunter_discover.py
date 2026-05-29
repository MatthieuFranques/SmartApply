"""Tests for Hunter /discover company fetch (requests mocked)."""

from unittest.mock import MagicMock, patch

from app.services.scraping import hunter_discover as hd


def _resp(data):
    r = MagicMock()
    r.raise_for_status.return_value = None
    r.json.return_value = {"data": data}
    return r


def test_discover_single_page_stops_when_under_limit():
    # 2 results (< limit 100) → single call then break
    with patch.object(hd, "get_country", return_value="FR"), \
         patch.object(hd.requests, "post", return_value=_resp([{"organization": "A"}, {"organization": "B"}])) as mock_post:
        out = hd.discover_companies("software", "Lyon", max_results=50)
    assert len(out) == 2
    assert mock_post.call_count == 1


def test_discover_empty_breaks():
    with patch.object(hd, "get_country", return_value="FR"), \
         patch.object(hd.requests, "post", return_value=_resp([])):
        out = hd.discover_companies("software", "Lyon", max_results=50)
    assert out == []


def test_discover_truncates_to_max_results():
    big = [{"organization": str(i)} for i in range(100)]
    with patch.object(hd, "get_country", return_value="FR"), \
         patch.object(hd.requests, "post", return_value=_resp(big)):
        out = hd.discover_companies("software", "Lyon", max_results=10)
    assert len(out) == 10


def test_discover_handles_request_error():
    with patch.object(hd, "get_country", return_value="FR"), \
         patch.object(hd.requests, "post", side_effect=Exception("network")):
        out = hd.discover_companies("software", "Lyon", max_results=50)
    assert out == []
