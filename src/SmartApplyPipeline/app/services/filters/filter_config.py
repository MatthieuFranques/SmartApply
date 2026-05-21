"""
filter_config.py
----------------
Toutes les constantes lisent d'abord le .env, avec valeurs par défaut.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TIMEOUT_HTTP = int(os.getenv("TIMEOUT_HTTP", "6"))
PAUSE        = float(os.getenv("PAUSE", "0.3"))
CONCURRENCY  = int(os.getenv("CONCURRENCY", "10"))
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}

MIN_PRESCORE   = int(os.getenv("MIN_PRESCORE", "4"))
MIN_DEEP_SCORE = int(os.getenv("MIN_DEEP_SCORE", "5"))

BLACKLIST = [
    "dentaire", "dental", "médecin", "clinique", "pharmacie",
    "kinésithérapie", "ophtalmo", "cabinet médical", "infirmier",
    "rénovation", "renovation", "plomberie", "électricité", "maçon",
    "peinture", "carrelage", "toiture", "bâtiment", "construction",
    "coiffure", "restaurant", "boulangerie", "immobilier", "assurance",
    "notaire", "avocat", "comptable", "expert-comptable",
    "école primaire", "collège", "lycée", "maternelle",
    "association sportive", "église", "paroisse",
    "salon de beauté", "esthétique", "massage",
]

IT_KEYWORDS = [
    ".net", "c#", "react", "vue", "angular", "typescript",
    "asp.net", "blazor", "azure", "dotnet",
    "développement", "development", "software", "logiciel",
    "informatique", "digital", "numérique", "cloud", "devops",
    "fullstack", "full-stack", "backend", "frontend",
    "application", "web app", "saas", "api", "microservices",
    "esn", "ssii", "consulting", "conseil it", "it services",
    "régie", "forfait", "mission", "prestataire", "outsourcing",
    "développeur", "developer", "ingénieur logiciel", "software engineer",
    "architecte",
]

CAREER_PATHS = [
    "/carrieres", "/carrières", "/recrutement", "/rejoindre-nous",
    "/nous-rejoindre", "/jobs", "/offres-emploi", "/offres",
    "/careers", "/work-with-us", "/join-us", "/hiring",
    "/join", "/team", "/equipe",
]

MX_PROVIDERS = {
    "google"   : "Google Workspace",
    "gmail"    : "Google Workspace",
    "outlook"  : "Microsoft 365",
    "microsoft": "Microsoft 365",
    "ovh"      : "OVH",
}

CITY_COUNTRY_MAP = {
    "Toulouse" : "FR",
    "Brussels" : "BE",
    "Namur"    : "BE",
    "Bruxelles": "BE",
}

SECTORS = [
    "informatique", "développement logiciel", "agence web",
    "startup tech", "cybersécurité", "intelligence artificielle",
    "cloud computing", "édition logiciel", "conseil digital",
    "transformation digitale", "fintech", "ESN", "SSII",
    "software development", "web agency", "tech startup",
    "digital consulting", "digital transformation",
    "IT services", "IT consulting", "technology",
]