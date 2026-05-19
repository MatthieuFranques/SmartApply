import chromadb
from app.config import CHROMA_PATH, COLLECTIONS
from app.services.embedder import embed_text

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return _client


def _get_collection(name: str):
    return _get_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert(collection_name: str, doc_id: str, text: str, metadata: dict) -> None:
    col = _get_collection(collection_name)
    embedding = embed_text(text)
    col.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata],
    )


def query(collection_name: str, query_text: str, k: int = 3) -> list[dict]:
    col = _get_collection(collection_name)
    count = col.count()
    if count == 0:
        return []

    embedding = embed_text(query_text)
    results = col.query(
        query_embeddings=[embedding],
        n_results=min(k, count),
        include=["documents", "metadatas", "distances"],
    )

    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas",  [[]])[0]
    dists = results.get("distances",  [[]])[0]

    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(docs, metas, dists)
    ]


def collection_count(collection_name: str) -> int:
    try:
        return _get_collection(collection_name).count()
    except Exception:
        return 0
