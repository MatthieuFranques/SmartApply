# ============================================================
# prompts.py
# Construction des prompts — 2 passes de génération
# ============================================================

from app.services.generate_letter.generate_letter_config  import REFERENCE_LETTER


def build_analysis_prompt(company: dict, profile: dict) -> str:
    """
    PASSE 1 — Analyse structurée profil vs entreprise.
    Temperature basse recommandée (0.3).
    """
    tech_list   = ", ".join(company.get("tech_keywords",    [])[:10]) or "non détectées"
    job_tech    = ", ".join(company.get("job_keywords",     [])[:8])  or "non disponibles"
    key_phrases = "\n".join(f"  - {p}" for p in company.get("key_phrases", [])[:4])
    description = company.get("description", "") or company.get("about_text", "")[:400]
    founded     = company.get("founded_hint", "") or "inconnue"

    # Résumé des offres pertinentes
    offers = company.get("job_offers", [])
    if offers:
        best_offers = offers[:3]  # Top 3 seulement
        offers_summary = "\n".join(
            f"  - [{o['relevance_score']}/10] {o['title']} | technos: {', '.join(o['tech_required'][:5]) or 'non précisées'}"
            for o in best_offers
        )
    else:
        offers_summary = "  Aucune offre parsée"

    # Infos formulaire de contact
    contact = company.get("contact_form", {})
    contact_info = ""
    if contact:
        contact_info = (
            f"URL contact : {contact.get('url', '')}\n"
            f"Upload fichier : {'oui' if contact.get('has_file_upload') else 'non'}\n"
            f"Email direct : {contact.get('email_found', 'non trouvé')}"
        )

    return f"""Tu es un directeur du recrutement avec 15 ans d'expérience, spécialisé dans les profils tech.
Ta mission : analyser la compatibilité entre un candidat et une entreprise, et identifier les arguments les plus percutants.

Raisonne étape par étape avant de conclure.

=== ENTREPRISE ===
Nom : {company['nom']}
Secteur : {company['secteur']}
Ville : {company['ville']}
Description : {description}
Taille estimée : {company.get('company_size_hint') or 'inconnue'}
Fondée en : {founded}
Technologies détectées : {tech_list}
Technologies dans leurs offres : {job_tech}
Phrases clés :
{key_phrases or '  (aucune)'}

Offres d'emploi détectées (triées par pertinence) :
{offers_summary}

{f"Formulaire de contact :{chr(10)}{contact_info}" if contact_info else ""}

=== CANDIDAT ===
Diplôme : {profile['diplome']} — {profile['ecole']} ({profile['annee']})
Expériences : {profile['experiences']}
Projet phare : {profile['projet_phare']}
Compétences : {profile['competences']}
Soft skills : {profile['soft_skills']}
Recherche : {profile['recherche']}
Localisation : {profile['ville']}

=== ANALYSE DEMANDÉE ===
Réponds exactement dans ce format :

ACCROCHE:
[1 phrase spécifique — si une offre est pertinente, fais référence à son intitulé exact]

EXPERIENCES_CLES:
[Les 2 expériences les plus pertinentes pour CETTE entreprise, avec pourquoi]

POINTS_FORTS:
- [Point fort 1 adapté à leur stack/secteur avec techno concrète]
- [Point fort 2 adapté à leur stack/secteur avec techno concrète]
- [Point fort 3 adapté à leur stack/secteur avec techno concrète]

TON:
[direct/startup OU formel/grand groupe — justifie en 1 phrase]

ANGLE_DIFFERENTIANT:
[Ce qui rend CE candidat unique pour CETTE entreprise — 1-2 phrases]

MODE:
[OFFRE si une offre pertinente existe (score >= 5) | SPONTANEE sinon]"""


def build_letter_prompt(company: dict, profile: dict, analysis: str) -> str:
    """
    PASSE 2 — Rédaction de la lettre.
    Temperature recommandée (0.7).

    Adapte automatiquement l'objet selon le MODE détecté dans l'analyse :
    - OFFRE      → mentionne l'intitulé exact du poste
    - SPONTANEE  → candidature spontanée générique
    """
    # Meilleure offre (si disponible)
    offers = company.get("job_offers", [])
    best_offer_title = offers[0]["title"] if offers else ""
    best_offer_url   = offers[0]["url"]   if offers else ""

    offer_context = ""
    if best_offer_title:
        offer_context = (
            f"Offre ciblée : {best_offer_title}\n"
            f"Lien de l'offre : {best_offer_url}\n"
            f"Technos requises : {', '.join(offers[0].get('tech_required', [])[:6])}"
        )

    return f"""Tu es un rédacteur expert en lettres de motivation pour profils tech en France/Belgique.

Ta seule tâche : rédiger une lettre de motivation en français.

=== LETTRE DE RÉFÉRENCE (ton, style, structure à reproduire) ===
{REFERENCE_LETTER}
=== FIN DE RÉFÉRENCE ===

=== ANALYSE PRÉALABLE ===
{analysis}
=== FIN DE L'ANALYSE ===

=== CONTEXTE ===
Entreprise : {company['nom']} | {company['secteur']} | {company['ville']}
{offer_context if offer_context else "Mode : candidature spontanée"}
Candidat : {profile['prenom_nom']} — {profile['diplome']} — {profile['ecole']} {profile['annee']}
Portfolio : {profile['portfolio']}
GitHub : {profile['github']}

=== STRUCTURE OBLIGATOIRE ===
1. "Objet :" — si MODE=OFFRE : "Candidature – [intitulé exact du poste] | {company['nom']}"
              si MODE=SPONTANEE : "Candidature spontanée – Développeur .NET/Fullstack | Disponible immédiatement"
2. Formule d'appel selon taille détectée
3. §1 Intro (3 phrases) : accroche sur {company['nom']} → qui je suis → disponibilité
4. §2 Expérience (4-5 phrases) : EXPERIENCES_CLES + ANGLE_DIFFERENTIANT de l'analyse
5. "Ce qui me distingue :" + 3 bullets des POINTS_FORTS
6. §3 Closing : Portfolio ({profile['portfolio']}) + GitHub ({profile['github']}) + dispo entretien
7. "Cordialement,"

=== INTERDICTIONS ABSOLUES ===
- NE PAS écrire l'en-tête (ajouté automatiquement)
- NE PAS utiliser : "j'ai l'honneur de", "veuillez agréer", "dynamique et motivé"
- NE PAS dépasser 330 mots
- NE PAS inventer des technologies non détectées
- NE PAS ajouter de commentaire autour de la lettre

=== COMMENCE DIRECTEMENT PAR "Objet :" ==="""


def build_contact_form_prompt(company: dict, profile: dict) -> str:
    """
    Prompt alternatif quand pas d'offre mais formulaire de contact détecté.
    Génère un JSON avec les informations à remplir dans le formulaire.
    """
    contact = company.get("contact_form", {})
    fields  = contact.get("fields", [])
    fields_desc = "\n".join(
        f"  - {f.get('type','text')} | name='{f.get('name','')}' | label='{f.get('label','')}'"
        for f in fields
    ) or "  Champs non détectés"

    return f"""Tu es expert en rédaction de messages de candidature professionnels.

Une entreprise a un formulaire de contact mais pas d'offre d'emploi ouverte.
Tu dois générer le contenu à remplir dans ce formulaire pour une candidature spontanée.

=== ENTREPRISE ===
Nom : {company['nom']}
Secteur : {company['secteur']}
Ville : {company['ville']}
Description : {company.get('description', '')}

=== FORMULAIRE DÉTECTÉ ===
URL : {contact.get('url', '')}
Upload fichier possible : {'oui' if contact.get('has_file_upload') else 'non'}
Email direct : {contact.get('email_found', 'non trouvé')}
Champs détectés :
{fields_desc}

=== CANDIDAT ===
Nom : {profile['prenom_nom']}
Diplôme : {profile['diplome']} — {profile['ecole']} ({profile['annee']})
Compétences : {profile['competences']}
GitHub : {profile['github']}
Portfolio : {profile['portfolio']}
Email : {profile['email']}
Téléphone : {profile['telephone']}

=== TÂCHE ===
Génère un JSON avec le contenu à remplir pour chaque champ du formulaire.
Format de réponse (JSON uniquement, sans markdown) :
{{
  "objet": "...",
  "message": "...(150-200 mots, direct et professionnel)...",
  "champs": {{
    "nom": "{profile['prenom_nom']}",
    "email": "{profile['email']}",
    "telephone": "{profile['telephone']}",
    "message": "...(même contenu que message ci-dessus)..."
  }},
  "fichiers_a_joindre": ["CV", "Portfolio"] si upload possible sinon [],
  "note": "conseil spécifique pour ce formulaire"
}}"""