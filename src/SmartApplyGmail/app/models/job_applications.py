from pydantic import BaseModel
from typing import Optional


class CandidatureItem(BaseModel):
    """Une candidature parsée depuis Gmail."""
    id:           str                  # ID unique du thread Gmail
    entreprise:   str
    poste:        str
    statut:       str                  # En attente | Refusé | Entretien | Offre reçue | Décision requise
    ville:        Optional[str] = ""
    date:         Optional[str] = ""   # ISO 8601
    expediteur:   Optional[str] = ""
    gmail_link:   Optional[str] = ""


class SyncResult(BaseModel):
    """Résultat d'une synchronisation Gmail."""
    total_analyses:  int
    nouvelles:       int
    mises_a_jour:    int
    ignorees:        int
    sans_poste:      int
    derniere_sync:   str