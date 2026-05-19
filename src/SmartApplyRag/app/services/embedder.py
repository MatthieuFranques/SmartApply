import ollama
from app.config import OLLAMA_HOST, EMBED_MODEL

_client = ollama.Client(host=OLLAMA_HOST)


def embed_text(text: str) -> list[float]:
    text = text.strip()[:2000]
    try:
        response = _client.embed(model=EMBED_MODEL, input=text)
        return response.embeddings[0]
    except Exception as e:
        raise RuntimeError(
            f"Embedding failed — is '{EMBED_MODEL}' pulled? Run: ollama pull {EMBED_MODEL}\n{e}"
        ) from e


def check_embed_model() -> bool:
    try:
        models = _client.list()
        names = [m.model for m in models.models]
        return any(EMBED_MODEL in n for n in names)
    except Exception:
        return False
