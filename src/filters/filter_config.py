"""
filter_config.py
----------------
Constantes partagées par prefilter.py et deep_filter.py.
Modifier ici pour affiner les filtres sans toucher à la logique.
"""

# ─── HTTP ────────────────────────────────────────────────────

TIMEOUT_HTTP = 6      # secondes max par requête
PAUSE        = 0.3    # pause entre chaque domaine (politeness)
CONCURRENCY  = 10     # workers async simultanés (deep_filter)
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}

# ─── SEUILS DE SCORE ─────────────────────────────────────────

MIN_PRESCORE   = 4    # score minimum pour passer au deep filter
MIN_DEEP_SCORE = 5    # score minimum pour passer au scoring Gemini

# ─── MOTS BLACKLISTÉS (hors cible IT) ────────────────────────

BLACKLIST = [
    # Santé / médical
    "dentaire", "dental", "médecin", "clinique", "pharmacie",
    "kinésithérapie", "ophtalmo", "cabinet médical", "infirmier",
    # BTP / rénovation
    "rénovation", "renovation", "plomberie", "électricité", "maçon",
    "peinture", "carrelage", "toiture", "bâtiment", "construction",
    # Autres hors cible
    "coiffure", "restaurant", "boulangerie", "immobilier", "assurance",
    "notaire", "avocat", "comptable", "expert-comptable",
    "école primaire", "collège", "lycée", "maternelle",
    "association sportive", "église", "paroisse",
    "salon de beauté", "esthétique", "massage",
]

# ─── MOTS-CLÉS IT POSITIFS ───────────────────────────────────
# Utilisés dans prefilter (pré-score) ET deep_filter (offres carrières).

IT_KEYWORDS = [
    # Stack ciblée
    ".net", "c#", "react", "vue", "angular", "typescript",
    "asp.net", "blazor", "azure", "dotnet",
    # Général IT
    "développement", "development", "software", "logiciel",
    "informatique", "digital", "numérique", "cloud", "devops",
    "fullstack", "full-stack", "backend", "frontend",
    "application", "web app", "saas", "api", "microservices",
    # ESN / SSII
    "esn", "ssii", "consulting", "conseil it", "it services",
    "régie", "forfait", "mission", "prestataire", "outsourcing",
    # Métiers (utilisés aussi pour détecter les offres IT)
    "développeur", "developer", "ingénieur logiciel", "software engineer",
    "architecte",
]

# ─── CHEMINS CARRIÈRES À TESTER ──────────────────────────────

CAREER_PATHS = [
    "/carrieres", "/carrières", "/recrutement", "/rejoindre-nous",
    "/nous-rejoindre", "/jobs", "/offres-emploi", "/offres",
    "/careers", "/work-with-us", "/join-us", "/hiring",
    "/join", "/team", "/equipe",
]

# ─── FOURNISSEURS MX CONNUS ──────────────────────────────────

MX_PROVIDERS = {
    "google"   : "Google Workspace",
    "gmail"    : "Google Workspace",
    "outlook"  : "Microsoft 365",
    "microsoft": "Microsoft 365",
    "ovh"      : "OVH",
}
