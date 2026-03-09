"""
filter_scoring.py
-----------------
Calcul des scores partagé entre prefilter.py et deep_filter.py.

compute_prescore  → utilisé par prefilter.py
compute_deep_score → utilisé par deep_filter.py
Les deux fonctions de détection de mots-clés sont aussi centralisées ici
car elles servent dans les deux pipelines.
"""

from filter_config import BLACKLIST, IT_KEYWORDS


# ─── DÉTECTION DE CONTENU ────────────────────────────────────

def detect_blacklist(text: str) -> str:
    """
    Cherche un mot blacklisté dans le texte.
    Retourne le premier mot trouvé, ou chaîne vide si aucun.
    Un seul mot suffit à éliminer l'entreprise.
    """
    text_lower = text.lower()
    for word in BLACKLIST:
        if word in text_lower:
            return word
    return ""


def count_it_keywords(text: str) -> tuple[int, list[str]]:
    """
    Compte les mots-clés IT positifs dans le texte.
    Retourne (nombre trouvé, liste des mots trouvés).
    """
    text_lower = text.lower()
    found = [kw for kw in IT_KEYWORDS if kw in text_lower]
    return len(found), found


# ─── PRÉ-SCORE (prefilter) ───────────────────────────────────

def compute_prescore(accessible: bool, blacklisted: str,
                     it_count: int, company: dict) -> int:
    """
    Calcule un pré-score de 0 à 10 basé sur les signaux gratuits du site.
    Utilisé par prefilter.py pour décider si l'entreprise mérite un deep filter.

    Barème :
        Site inaccessible        → 0
        Mot blacklisté           → 1
        0 mot-clé IT             → 3  (incertain)
        1-2 mots-clés IT         → 6  (probable)
        3+ mots-clés IT          → 8  (très probable)
        Secteur Hunter IT        → +1 bonus
    """
    if not accessible:
        return 0
    if blacklisted:
        return 1

    score = 3

    if it_count >= 3:
        score = 8
    elif it_count >= 1:
        score = 6

    # Bonus secteur Hunter
    sector = company.get("secteur", "").lower()
    if any(kw in sector for kw in ["software", "it ", "informatique", "tech", "digital", "esn"]):
        score = min(score + 1, 10)

    return score


# ─── DEEP SCORE (deep_filter) ────────────────────────────────

def compute_deep_score(freshness: dict, mx: dict,
                       careers: dict, prescore: int) -> int:
    """
    Calcule le score final de 0 à 10 à partir des 3 couches du deep filter.
    Utilisé par deep_filter.py.

    Pondération :
        Pré-score existant   → base
        Page carrières IT    → +3
        Page carrières seule → +1
        MX valide            → +1
        Site frais           → +1

    Filtres durs :
        Pas de page carrières     → score plafonné à 4 (éliminé)
        Carrières sans offres IT  → score plafonné à 6
    """
    score  = prescore
    score += careers.get("career_score", 0)
    score += 1 if mx.get("has_mx")       else 0
    score += 1 if freshness.get("fresh") else 0
    score  = min(score, 10)

    if not careers.get("has_careers"):
        score = min(score, 4)
    elif not careers.get("it_jobs_found"):
        score = min(score, 6)

    return score
