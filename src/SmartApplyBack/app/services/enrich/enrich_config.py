# ============================================================
# enrich_config.py
# Constantes, mots-clés et structures de données
# ============================================================

from dataclasses import dataclass, field


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

TIMEOUT = 10
DELAY_BETWEEN_REQUESTS = 1.5


# --- Technologies à détecter ---
TECH_KEYWORDS = [
    "python", "javascript", "typescript", "react", "vue", "angular",
    "node.js", "nodejs", "django", "flask", "fastapi", "laravel", "symfony",
    "java", "spring", "kotlin", "swift", "rust", "go", "golang", "php",
    "docker", "kubernetes", "aws", "azure", "gcp", "devops", "ci/cd",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "machine learning", "deep learning", "ia", "intelligence artificielle",
    "data science", "big data", "power bi", "tableau", "spark",
    "api", "rest", "graphql", "microservices", "cloud", "serverless",
    "linux", "git", "github", "gitlab", "agile", "scrum",
    "blazor", ".net", "c#", "flutter", "next.js", "nextjs",
]

# --- Indices de taille ---
SIZE_HINTS = {
    "startup":        "Startup",
    "scale-up":       "Scale-up",
    "pme":            "PME",
    "tpe":            "TPE",
    "grand groupe":   "Grand groupe",
    "multinationale": "Multinationale",
    "filiale":        "Filiale",
    "groupe":         "Groupe",
    "collaborateurs": "PME/Groupe",
    "salariés":       "PME/Groupe",
    "employés":       "PME/Groupe",
}

# --- Intitulés de postes IT ---
JOB_TITLE_KEYWORDS = [
    "développeur", "developer", "dev", "ingénieur", "engineer",
    "fullstack", "full stack", "full-stack",
    "frontend", "front-end", "front end",
    "backend", "back-end", "back end",
    "mobile", "ios", "android", "flutter",
    "devops", "sre", "cloud", "data",
    "architecte", "architect",
    "lead", "senior", "junior", "stagiaire", "alternant",
    ".net", "blazor", "python", "java", "go", "react", "vue",
    "consultant", "analyste", "analyst",
]

# --- Mots-clés profil candidat pour scorer la pertinence d'une offre ---
CANDIDATE_KEYWORDS = [
    ".net", "blazor", "c#", "flutter", "next.js", "nextjs",
    "vue", "react", "javascript", "typescript",
    "python", "docker", "git", "agile", "sql", "api",
    "fullstack", "full stack", "full-stack",
    "mobile", "web", "cloud", "aws",
]

# --- Chemins typiques de pages contact ---
CONTACT_PATHS = [
    "/contact", "/nous-contacter", "/contact-us",
    "/contactez-nous", "/get-in-touch", "/reach-us",
    "/about#contact", "/a-propos#contact",
]


@dataclass
class JobOffer:
    """Représente une offre d'emploi individuelle."""
    title:       str = ""   # Intitulé du poste
    url:         str = ""   # Lien direct vers l'offre
    description: str = ""   # Description extraite
    tech_required: list = field(default_factory=list)  # Technos mentionnées
    relevance_score: int = 0  # Score de pertinence vs profil candidat (0-10)


@dataclass
class ContactForm:
    """Informations sur le formulaire de contact."""
    url:            str  = ""    # URL de la page contact
    has_file_upload: bool = False # Accepte-t-il des fichiers (CV/portfolio) ?
    fields:         list = field(default_factory=list)  # Champs détectés
    email_found:    str  = ""    # Email de contact direct si trouvé


@dataclass
class CompanyContext:
    # --- Données brutes du CSV ---
    nom:          str
    domaine:      str
    ville:        str
    secteur:      str
    careers_url:  str = ""
    site_title:   str = ""

    # --- Données enrichies ---
    description:       str  = ""
    about_text:        str  = ""
    tech_keywords:     list = field(default_factory=list)
    job_keywords:      list = field(default_factory=list)
    job_titles_found:  list = field(default_factory=list)
    key_phrases:       list = field(default_factory=list)
    company_size_hint: str  = ""
    founded_hint:      str  = ""
    is_recruiting:     bool = False

    # --- Offres d'emploi détaillées ---
    # Liste de dicts (JobOffer sérialisé) triés par pertinence
    job_offers:        list = field(default_factory=list)

    # --- Formulaire de contact (si pas d'offre pertinente) ---
    # Dict (ContactForm sérialisé) ou vide
    contact_form:      dict = field(default_factory=dict)

    # --- Statut ---
    scrape_status: str = ""
    scrape_error:  str = ""