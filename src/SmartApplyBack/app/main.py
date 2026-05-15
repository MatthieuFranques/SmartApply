from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.indexes import create_indexes
from app.routers import scraping, filter, enrich, letter, gmail, job_applications, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_indexes()
    yield


app = FastAPI(title="SmartApply API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth.router)
app.include_router(scraping.router)
app.include_router(filter.router)
app.include_router(enrich.router)
app.include_router(letter.router)
app.include_router(gmail.router)
app.include_router(job_applications.router)