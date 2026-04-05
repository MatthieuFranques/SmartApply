from pydantic import BaseModel, Field
from typing import Optional, Any, List 
from datetime import datetime

class ContactForm(BaseModel):
    url: str = ""
    has_file_upload: bool = False
    fields: list[dict] = [] 
    email_found: str = ""

class Job(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    stage: str = "scraping"  
    status: str = "active"    
    nom: str = ""
    domaine: str = ""
    ville: str = ""
    secteur: str = ""
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