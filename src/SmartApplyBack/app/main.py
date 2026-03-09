# app/main.py
from fastapi import FastAPI
from app.routers import scraping, filter,  enrich
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="SmartApply API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraping.router)
app.include_router(filter.router)
app.include_router(enrich.router)
# python -m uvicorn app.main:app --reload