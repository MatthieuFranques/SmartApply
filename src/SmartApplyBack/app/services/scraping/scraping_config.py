import os
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
MAX_WORKERS    = 5

CITY_COUNTRY_MAP = {
    "Toulouse"  : "FR",
    "Paris"     : "FR",
    "Lyon"      : "FR",
    "Bordeaux"  : "FR",
    "Nantes"    : "FR",
    "Lille"     : "FR",
    "Marseille" : "FR",
    "Brussels"  : "BE",
    "Bruxelles" : "BE",
    "Namur"     : "BE",
    "Liège"     : "BE",
    "Gent"      : "BE",
    "Antwerp"   : "BE",
    "Geneva"    : "CH",
    "Zurich"    : "CH",
    "Luxembourg": "LU",
    "London"    : "GB",
    "Berlin"    : "DE",
    "Amsterdam" : "NL",
    "Madrid"    : "ES",
    "Barcelona" : "ES",
}

DEFAULT_SECTORS = [
    "informatique",
    "développement logiciel",
    "agence web",
    "startup tech",
    "cybersécurité",
    "intelligence artificielle",
    "cloud computing",
    "édition logiciel",
    "conseil digital",
    "transformation digitale",
    "fintech",
    "ESN",
    "SSII",
]


def get_country(city: str, fallback: str = "FR") -> str:
    return CITY_COUNTRY_MAP.get(city, fallback)