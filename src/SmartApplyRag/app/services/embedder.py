import ollama
from app.config import OLLAMA_HOST, EMBED_MODEL

_client = ollama.Client(host=OLLAMA_HOST)


def embed_text(text: str) -> list[float]:
    text = text.strip()[:2000]
    try:
        response = _client.embeddings(model=EMBED_MODEL, prompt=text)
        return response["embedding"]
    except Exception as e:
        raise RuntimeError(
            f"Embedding failed — is '{EMBED_MODEL}' pulled? Run: ollama pull {EMBED_MODEL}\n{e}"
        ) from e


def check_embed_model() -> bool:
    try:
        embed_text("ping")
        return True
    except Exception:
        return False
