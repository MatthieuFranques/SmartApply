from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import COLLECTIONS, DEFAULT_USER_ID
from app.routers import generate, index, ingest, retrieve
from app.services.embedder import check_embed_model
from app.services.ingestor import ingest_inbox
from app.services.vector_store import collection_count


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-ingère les fichiers de l'inbox au démarrage
    try:
        results = ingest_inbox(DEFAULT_USER_ID)
        total = len(results["cvs"]) + len(results["letters"])
        if total:
            print(f"[RAG] Startup ingestion: {len(results['cvs'])} CV(s), {len(results['letters'])} lettre(s)")
        if results["errors"]:
            print(f"[RAG] Ingestion errors: {results['errors']}")
    except Exception as e:
        print(f"[RAG] Startup ingestion failed: {e}")
    yield


app = FastAPI(
    title="SmartApply RAG",
    description="RAG microservice — cover letter retrieval & indexing",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(generate.router)
app.include_router(index.router)
app.include_router(retrieve.router)
app.include_router(ingest.router)


@app.get("/health")
def health():
    embed_ok = check_embed_model()
    return {
        "status":            "ok" if embed_ok else "degraded",
        "embed_model_ready": embed_ok,
        "collections": {
            name: collection_count(col)
            for name, col in COLLECTIONS.items()
        },
    }
