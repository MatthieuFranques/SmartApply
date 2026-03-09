"""
gmail_drafts.py
---------------
Crée automatiquement des brouillons Gmail pour chaque entreprise.
Chaque brouillon contient :
  - Le destinataire (email de l'entreprise)
  - Un objet personnalisé généré par Gemini
  - La lettre de motivation dans le corps du mail
  - Le CV en pièce jointe (PDF)

Pré-requis : activer Gmail API sur Google Cloud Console +
             télécharger credentials.json dans le dossier du projet.
"""

import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from dotenv               import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials      import Credentials
from google_auth_oauthlib.flow      import InstalledAppFlow
from googleapiclient.discovery      import build

# ─── Chargement des variables d'environnement ───────────────────────────────
load_dotenv()

SCOPES           = ["https://www.googleapis.com/auth/gmail.compose"]
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE       = os.getenv("GMAIL_TOKEN_FILE", "token.json")
CV_PDF_PATH      = os.getenv("CV_PDF_PATH", "mon_cv.pdf")
SENDER_NAME      = os.getenv("SENDER_NAME", "Prénom NOM")
SENDER_EMAIL     = os.getenv("SENDER_EMAIL", "")


# ─── AUTHENTIFICATION ────────────────────────────────────────────────────────

def get_gmail_service():
    """
    Authentifie l'utilisateur via OAuth2 et retourne le service Gmail API.
    - Première exécution : ouvre le navigateur pour autoriser l'accès Gmail
    - Exécutions suivantes : réutilise le token sauvegardé (token.json)
    Le scope "gmail.compose" permet uniquement de créer des brouillons
    (pas de lire/supprimer les mails → sécurité maximale).

    Retourne :
        Service Gmail API authentifié, prêt à être utilisé.
    """
    creds = None

    # Charge le token existant si disponible
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Si pas de token valide, lance l'authentification OAuth2
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Sauvegarde le token pour les prochaines exécutions
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── CONSTRUCTION DU MAIL ────────────────────────────────────────────────────

def build_email_message(to: str, subject: str, body: str, cv_path: str) -> MIMEMultipart:
    """
    Construit le message email complet avec corps de texte et pièce jointe PDF.
    Utilise le format MIME multipart pour combiner texte + pièce jointe.
    Ajoute une signature automatique avec le nom et l'email de l'expéditeur
    chargés depuis le fichier .env.

    Paramètres :
        to      : adresse email du destinataire
        subject : objet du mail
        body    : corps du mail (lettre de motivation)
        cv_path : chemin vers le fichier PDF du CV

    Retourne :
        Objet MIMEMultipart représentant le mail complet, prêt à être encodé.
    """
    msg = MIMEMultipart()
    msg["To"]      = to
    msg["Subject"] = subject

    # Signature automatique ajoutée sous la lettre
    signature = f"\n\n--\n{SENDER_NAME}\n{SENDER_EMAIL}"
    full_body  = body + signature

    # Corps du mail = lettre de motivation + signature
    msg.attach(MIMEText(full_body, "plain", "utf-8"))

    # Pièce jointe = CV en PDF
    if cv_path and os.path.exists(cv_path):
        with open(cv_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(cv_path)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
    else:
        print(f"  ⚠️  CV introuvable : {cv_path} — brouillon créé sans pièce jointe")

    return msg


def encode_message(message: MIMEMultipart) -> dict:
    """
    Encode le message MIME en base64 URL-safe, format attendu par l'API Gmail
    pour la création de brouillons.

    Paramètres :
        message : objet MIMEMultipart représentant le mail

    Retourne :
        Dict {"message": {"raw": "<base64 encodé>"}} à passer à l'API Gmail.
    """
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"message": {"raw": raw}}


# ─── CRÉATION DES BROUILLONS ─────────────────────────────────────────────────

def create_draft(service, to: str, subject: str, body: str, cv_path: str = CV_PDF_PATH) -> dict:
    """
    Crée un seul brouillon Gmail pour une entreprise donnée.
    Le brouillon apparaît dans l'onglet Brouillons de Gmail,
    prêt à être relu et envoyé manuellement.

    Paramètres :
        service  : service Gmail API authentifié (retourné par get_gmail_service)
        to       : email du destinataire
        subject  : objet du mail
        body     : corps du mail (lettre de motivation)
        cv_path  : chemin vers le CV PDF à joindre

    Retourne :
        Réponse de l'API Gmail (dict) contenant l'ID du brouillon créé.
    """
    message = build_email_message(to, subject, body, cv_path)
    encoded = encode_message(message)
    draft   = service.users().drafts().create(userId="me", body=encoded).execute()
    return draft


def create_all_drafts(companies: list, cv_path: str = CV_PDF_PATH) -> None:
    """
    Boucle sur toutes les entreprises et crée un brouillon Gmail pour chacune.
    Ignore les entreprises sans adresse email connue.
    Affiche un résumé final : brouillons créés vs ignorés.

    Paramètres :
        companies : liste de dicts enrichis (avec clés 'lettre', 'objet_mail', 'email')
        cv_path   : chemin vers le CV PDF à joindre à chaque mail
    """
    service = get_gmail_service()
    created = 0
    skipped = 0
    total   = len(companies)

    for i, company in enumerate(companies, 1):
        name    = company.get("nom", "?")
        email   = company.get("email", "")
        letter  = company.get("lettre", "")
        subject = company.get("objet_mail", f"Candidature spontanée – {name}")

        if not email:
            print(f"  ⏭️  [{i}/{total}] {name} — pas d'email, ignoré")
            skipped += 1
            continue

        print(f"\n📨 [{i}/{total}] Brouillon pour {name} → {email}")
        try:
            draft = create_draft(service, email, subject, letter, cv_path)
            print(f"  ✅ Brouillon créé (ID: {draft.get('id')})")
            created += 1
        except Exception as e:
            print(f"  ❌ Erreur pour {name} : {e}")
            skipped += 1

    print(f"\n🎉 Terminé ! {created} brouillons créés, {skipped} ignorés.")
    print("👉 Va dans Gmail → Brouillons pour vérifier et envoyer !")