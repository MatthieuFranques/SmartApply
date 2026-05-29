"""Shared test config for the RAG microservice.

The vector store and generator import heavy optional deps (`chromadb`,
`ollama`) at module load. Unit tests don't touch the real DB or model — they
patch `upsert` / `query` / `_chat` — so we stub those modules in sys.modules
when they're not installed. This keeps the suite offline and CI-friendly.
"""

import sys
from unittest.mock import MagicMock

for _mod in ("chromadb", "ollama"):
    try:
        __import__(_mod)
    except ImportError:
        sys.modules[_mod] = MagicMock()
