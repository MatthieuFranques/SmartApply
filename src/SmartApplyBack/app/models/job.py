from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ContactForm(BaseModel):
    url: str = ""
    has_file_upload: bool = False
    fields: list[str] = []
    email_found: str = ""


class Job(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str                              # ← clé de tout

    # ── Champs communs à tous les stages ──
    nom: str
    domaine: str
    ville: str
    secteur: str
    email: str = ""

    # ── Stage actuel dans la pipeline ──
    stage: str = "scraping"
    # valeurs : scraping | filtered | deep | enriched
    status: str = "active"
    # valeurs : active | eliminated

    # ── Filter stage (prescore) ──
    prescore: Optional[int] = None
    site_title: Optional[str] = None
    site_desc: Optional[str] = None
    it_keywords: Optional[str] = None

    # ── Deep stage ──
    deep_score: Optional[int] = None
    has_mx: Optional[bool] = None
    mx_provider: Optional[str] = None
    has_careers: Optional[bool] = None
    it_jobs_found: Optional[bool] = None
    careers_url: Optional[str] = None

    # ── Enriched stage ──
    description: Optional[str] = None
    about_text: Optional[str] = None
    tech_keywords: list[str] = []
    job_keywords: list[str] = []
    job_titles_found: list[str] = []
    key_phrases: list[str] = []
    company_size_hint: Optional[str] = None
    founded_hint: Optional[str] = None
    is_recruiting: Optional[bool] = None
    job_offers: list[dict] = []
    contact_form: Optional[ContactForm] = None
    scrape_status: Optional[str] = None
    scrape_error: Optional[str] = None

    # ── Timestamps ──
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True