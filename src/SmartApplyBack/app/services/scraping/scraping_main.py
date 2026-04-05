# app/services/scraping/scraping_main.py

import os
import sys
from datetime import datetime

# Garde tes imports de path si nécessaire pour scraper
sys.path.insert(0, os.path.dirname(__file__))
from scraper import scrape_companies

SECTORS = [
    "informatique", "développement logiciel", "agence web",
    "startup tech", "cybersécurité", "intelligence artificielle",
    "cloud computing", "édition logiciel", "conseil digital",
    "transformation digitale", "fintech", "ESN", "SSII",
]

def stream_scraping(cities: list[str], user_id: str, repo):
    """
    Générateur pour le flux SSE. 
    Prend 3 arguments comme appelé dans le routeur.
    """
    seen_domains: set[str] = set()
    total_found = 0
    print(f"DEBUG: Lancement du stream pour {user_id} dans {cities}")
    # 1. Signaler le début au Frontend
    yield {"type": "phase", "status": "started", "phase": "scraping"}

    for city in cities:
        yield {"type": "info", "message": f"Recherche en cours à {city}..."}
        
        for sector in SECTORS:
            # Appel au script de scraping pur
            results = scrape_companies(sector, [city])

            for company in results:
                domaine = company.get("domaine")
                
                if domaine and domaine not in seen_domains:
                    seen_domains.add(domaine)
                    total_found += 1
                    
                    # 2. Sauvegarde en DB via JobRepository (Utilise save_many avec une liste d'un seul item)
                    # Ton repo n'a pas de 'save_one', donc on utilise save_many avec [company]
                    repo.save_many([company], user_id, stage="scraping")

                    # 3. Envoie l'info au Frontend en temps réel
                    yield {
                        "type": "company",
                        "phase": "scraping",
                        "company": company.get("nom", domaine),
                        "domaine": domaine,
                        "city": city
                    }

    # 4. Signaler la fin du process
    yield {
        "type": "done",
        "phase": "scraping",
        "total": total_found
    }