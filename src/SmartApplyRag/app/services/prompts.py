def build_header(profile: dict) -> str:
    parts = [profile.get("prenom_nom", "")]
    if profile.get("titre"):
        parts.append(profile["titre"])
    contact = " | ".join(filter(None, [profile.get("telephone"), profile.get("email")]))
    if contact:
        parts.append(contact)
    if profile.get("portfolio"):
        parts.append(f"Portfolio : {profile['portfolio']}")
    if profile.get("github"):
        parts.append(f"GitHub : {profile['github']}")
    return "\n".join(parts)


def build_analysis_prompt(company: dict, profile: dict, cv_chunks: list[str] | None = None) -> str:
    tech_list   = ", ".join(company.get("tech_keywords",    [])[:10]) or "non détectées"
    job_tech    = ", ".join(company.get("job_keywords",     [])[:8])  or "non disponibles"
    key_phrases = "\n".join(f"  - {p}" for p in company.get("key_phrases", [])[:4])
    description = company.get("description", "") or company.get("about_text", "")[:400]
    founded     = company.get("founded_hint", "") or "inconnue"

    offers = company.get("job_offers", [])
    if offers:
        offers_summary = "\n".join(
            f"  - [{o['relevance_score']}/10] {o['title']} | technos: {', '.join(o.get('tech_required', [])[:5]) or 'non précisées'}"
            for o in offers[:3]
        )
    else:
        offers_summary = "  Aucune offre parsée"

    contact = company.get("contact_form", {})
    contact_info = ""
    if contact:
        contact_info = (
            f"URL contact : {contact.get('url', '')}\n"
            f"Upload fichier : {'oui' if contact.get('has_file_upload') else 'non'}\n"
            f"Email direct : {contact.get('email_found', 'non trouvé')}"
        )

    # Enrichissement RAG : chunks CV pertinents
    cv_context = ""
    if cv_chunks:
        cv_context = "\n=== EXTRAITS CV PERTINENTS (RAG) ===\n"
        cv_context += "\n---\n".join(cv_chunks[:3])

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
Diplôme : {profile.get('diplome', '')} — {profile.get('ecole', '')} ({profile.get('annee', '')})
Expériences : {profile.get('experiences', '')}
Projet phare : {profile.get('projet_phare', '')}
Compétences : {profile.get('competences', '')}
Soft skills : {profile.get('soft_skills', '')}
Recherche : {profile.get('recherche', '')}
Localisation : {profile.get('ville', '')}
{cv_context}

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


def build_letter_prompt(
    company: dict,
    profile: dict,
    analysis: str,
    reference_letter: str = "",
    rag_context: dict | None = None,
) -> str:
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

    # Sélection de la référence : RAG > paramètre > aucune
    ref_section = ""
    if rag_context and rag_context.get("reference_letters"):
        ref = rag_context["reference_letters"][0]
        ref_section = f"=== LETTRE DE RÉFÉRENCE (RAG) ===\n{ref}\n=== FIN DE RÉFÉRENCE ==="
    elif reference_letter.strip():
        ref_section = f"=== LETTRE DE RÉFÉRENCE ===\n{reference_letter.strip()}\n=== FIN DE RÉFÉRENCE ==="

    # Lettres similaires passées comme exemples de style supplémentaires
    similar_section = ""
    if rag_context and rag_context.get("similar_letters"):
        similar_section = "=== LETTRES PASSÉES SIMILAIRES (même secteur/stack — style à reproduire) ===\n"
        similar_section += "\n---\n".join(rag_context["similar_letters"][:2])
        similar_section += "\n=== FIN DES EXEMPLES ==="

    return f"""Tu es un rédacteur expert en lettres de motivation pour profils tech en France/Belgique.

Ta seule tâche : rédiger une lettre de motivation en français.

{ref_section}

{similar_section}

=== ANALYSE PRÉALABLE ===
{analysis}
=== FIN DE L'ANALYSE ===

=== CONTEXTE ===
Entreprise : {company['nom']} | {company['secteur']} | {company['ville']}
{offer_context if offer_context else "Mode : candidature spontanée"}
Candidat : {profile.get('prenom_nom', '')} — {profile.get('diplome', '')} — {profile.get('ecole', '')} {profile.get('annee', '')}
Portfolio : {profile.get('portfolio', '')}
GitHub : {profile.get('github', '')}

=== STRUCTURE OBLIGATOIRE ===
1. "Objet :" — si MODE=OFFRE : "Candidature – [intitulé exact du poste] | {company['nom']}"
              si MODE=SPONTANEE : "Candidature spontanée – {profile.get('recherche', 'Développeur')} | Disponible immédiatement"
2. Formule d'appel selon taille détectée
3. §1 Intro (3 phrases) : accroche sur {company['nom']} → qui je suis → disponibilité
4. §2 Expérience (4-5 phrases) : EXPERIENCES_CLES + ANGLE_DIFFERENTIANT de l'analyse
5. "Ce qui me distingue :" + 3 bullets des POINTS_FORTS
6. §3 Closing : Portfolio ({profile.get('portfolio', '')}) + GitHub ({profile.get('github', '')}) + dispo entretien
7. "Cordialement,"

=== INTERDICTIONS ABSOLUES ===
- NE PAS écrire l'en-tête (ajouté automatiquement)
- NE PAS utiliser : "j'ai l'honneur de", "veuillez agréer", "dynamique et motivé"
- NE PAS dépasser 330 mots
- NE PAS inventer des technologies non détectées
- NE PAS ajouter de commentaire autour de la lettre

=== COMMENCE DIRECTEMENT PAR "Objet :" ==="""


def build_contact_form_prompt(company: dict, profile: dict) -> str:
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
Nom : {profile.get('prenom_nom', '')}
Diplôme : {profile.get('diplome', '')} — {profile.get('ecole', '')} ({profile.get('annee', '')})
Compétences : {profile.get('competences', '')}
GitHub : {profile.get('github', '')}
Portfolio : {profile.get('portfolio', '')}
Email : {profile.get('email', '')}
Téléphone : {profile.get('telephone', '')}

=== TÂCHE ===
Génère un JSON avec le contenu à remplir pour chaque champ du formulaire.
Format de réponse (JSON uniquement, sans markdown) :
{{
  "objet": "...",
  "message": "...(150-200 mots, direct et professionnel)...",
  "champs": {{
    "nom": "{profile.get('prenom_nom', '')}",
    "email": "{profile.get('email', '')}",
    "telephone": "{profile.get('telephone', '')}",
    "message": "...(même contenu que message ci-dessus)..."
  }},
  "fichiers_a_joindre": ["CV", "Portfolio"],
  "note": "conseil spécifique pour ce formulaire"
}}"""
