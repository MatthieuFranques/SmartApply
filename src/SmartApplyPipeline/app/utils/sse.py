import json
from typing import Any

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Access-Control-Allow-Origin": "http://localhost:4200",
}


def sse_event(data: Any) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"