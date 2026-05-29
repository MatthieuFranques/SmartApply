"""Unit tests for the SSE event formatter."""

import json

from app.utils.sse import sse_event, SSE_HEADERS


def test_sse_event_format():
    out = sse_event({"type": "progress", "value": 1})
    assert out.startswith("data: ")
    assert out.endswith("\n\n")
    payload = json.loads(out[len("data: "):].strip())
    assert payload == {"type": "progress", "value": 1}


def test_sse_event_keeps_unicode():
    """ensure_ascii=False → accents stay readable, not escaped."""
    out = sse_event({"msg": "éliminé"})
    assert "éliminé" in out


def test_sse_headers_disable_buffering():
    assert SSE_HEADERS["Cache-Control"] == "no-cache"
    assert SSE_HEADERS["X-Accel-Buffering"] == "no"
