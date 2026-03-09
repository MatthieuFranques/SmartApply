# app/main.py
from fastapi import FastAPI
from app.routers import scraping, filter,  enrich

app = FastAPI(title="SmartApply API")

app.include_router(scraping.router)
app.include_router(filter.router)
app.include_router(enrich.router)
# python -m uvicorn app.main:app --reload