import os
from pathlib import Path

OLLAMA_HOST      = os.getenv("OLLAMA_HOST",      "http://localhost:11434")
EMBED_MODEL      = os.getenv("EMBED_MODEL",      "nomic-embed-text")
CHROMA_PATH      = Path(os.getenv("CHROMA_PATH", "./data/chroma"))
INBOX_PATH       = Path(os.getenv("INBOX_PATH",  "./data/inbox"))
DEFAULT_USER_ID  = os.getenv("DEFAULT_USER_ID",  "default")
TOP_K_LETTERS    = int(os.getenv("TOP_K_LETTERS", "3"))
TOP_K_CV         = int(os.getenv("TOP_K_CV",      "3"))
TOP_K_REFS       = int(os.getenv("TOP_K_REFS",    "2"))

COLLECTIONS = {
    "letters":    "letters",
    "cv_chunks":  "cv_chunks",
    "companies":  "companies",
    "references": "references",
}
