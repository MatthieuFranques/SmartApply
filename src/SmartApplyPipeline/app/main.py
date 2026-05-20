from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.indexes import create_indexes
from app.routers import scraping, filter, enrich, pipeline, letter


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_indexes()
    yield


app = FastAPI(title="SmartApply Pipeline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(scraping.router)
app.include_router(filter.router)
app.include_router(enrich.router)
app.include_router(pipeline.router)
app.include_router(letter.router)
