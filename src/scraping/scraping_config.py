import os
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
OUTPUT_CSV     = os.getenv("CSV_OUTPUT_FILE", "entreprises.csv")
MAX_WORKERS    = 5  # appels parallèles max (respecte le rate limit Hunter)

CITY_COUNTRY_MAP = {
    "Toulouse"  : "FR",
    "Brussels"  : "BE",
    "Namur"     : "BE",
    "Bruxelles" : "BE",
}
