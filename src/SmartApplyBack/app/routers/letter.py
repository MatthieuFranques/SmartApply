import datetime
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.services.generate_letter.generate_letter_generator import (
    check_ollama,
    determine_mode,
    generate_contact_form,
    generate_letter,
    load_json,
    save_contact_form,
    save_letter,
)
from app.models.letter import (
    DEFAULT_MODEL,
    OUTPUT_DIR,
    INPUT_FILE,
    CompanySearchRequest,
    GenerateRequest,
    GenerateResponse,
    LetterItem,
)

# Utilisation d'un préfixe propre
router = APIRouter(prefix="/letter", tags=["letter"])

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Helpers (Inchangés mais inclus pour la cohérence) ─────────────────────────

def find_company(name: str, input_file: str | None) -> dict:
    resolved_file = Path(input_file) if input_file else INPUT_FILE
    
    # DEBUG: On vérifie l'existence réelle avant de charger
    if not resolved_file.exists():
        # On liste les fichiers présents pour t'aider à debugger
        parent_dir = resolved_file.parent
        existing_files = list(parent_dir.glob("*")) if parent_dir.exists() else "Dossier parent introuvable"
        raise HTTPException(
            status_code=404, 
            detail={
                "error": "Fichier introuvable",
                "asked_path": str(resolved_file.absolute()),
                "directory_content": [f.name for f in existing_files] if isinstance(existing_files, list) else existing_files
            }
        )

    try:
        companies = load_json(resolved_file)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erreur lecture JSON : {e}")

    # Recherche
    matches = [c for c in companies if name.lower() in c.get("nom", "").lower()]
    
    if not matches:
        # On donne la liste des noms dispos pour corriger le curl
        available_names = [c.get("nom") for c in companies[:5]] # top 5
        raise HTTPException(
            status_code=404, 
            detail=f"Entreprise '{name}' non trouvée. Exemples dispo : {available_names}"
        )
        
    if len(matches) > 1:
        raise HTTPException(status_code=409, detail="Plusieurs entreprises trouvées.")
        
    return matches[0]


def resolve_output_dir(output_dir: str) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def find_generated_file(name: str, output_dir: Path) -> Path:
    slug = name.lower().replace(" ", "_")
    candidates = list(output_dir.glob(f"{slug}*.txt")) + list(output_dir.glob(f"{slug}*.json"))
    if not candidates:
        raise HTTPException(status_code=404, detail=f"Aucun fichier pour '{name}'.")
    return max(candidates, key=lambda p: p.stat().st_mtime)

# ── Routes ────────────────────────────────────────────────────────────────────

# Correction : On définit la route sur "" (qui devient /letter avec le préfixe)
# ou sur "/" (qui devient /letter/).
@router.post("/", response_model=GenerateResponse, status_code=201)
def generate(body: GenerateRequest):
    if not check_ollama():
        raise HTTPException(status_code=503, detail="Ollama inaccessible.")

    company    = find_company(body.name, body.input_file)
    output_dir = resolve_output_dir(body.output_dir)
    mode       = determine_mode(company)

    # Nettoyage du nom pour le nom de fichier (on enlève les espaces/caractères spéciaux)
    safe_name = "".join(x for x in company["nom"] if x.isalnum() or x in "._- ")
    filename  = f"{safe_name}.json"
    filepath  = output_dir / filename

    try:
        # On génère le contenu
        if mode == "contact":
            content = generate_contact_form(company, body.model)
            mode_label = "contact"
        else:
            content = generate_letter(company, body.model)
            offers = company.get("job_offers", [])
            mode_label = "letter_targeted" if offers else "letter_spontaneous"

        # Création de l'objet JSON complet pour l'entreprise
        data_to_save = {
            "company": company["nom"],
            "date": datetime.date.today().isoformat(),
            "mode": mode_label,
            "model": body.model,
            "content": content,
            "metadata": {
                "domaine": company.get("domaine"),
                "ville": company.get("ville")
            }
        }

        # Sauvegarde directe en format JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde : {e}")

    return GenerateResponse(
        company=company["nom"],
        filename=filename,
        mode=mode_label,
        model=body.model,
        output_dir=str(output_dir),
    )

@router.get("/details")  # On change un peu l'URL pour ne pas confondre avec /{name}
def get_letter_by_body(request: CompanySearchRequest, output_dir: str = Query(default=str(OUTPUT_DIR))):
    # On utilise find_generated_file avec le nom passé dans le body
    path = find_generated_file(request.name, Path(output_dir))
    
    # Si c'est un JSON, on peut soit renvoyer le fichier, 
    # soit renvoyer directement le contenu JSON structuré
    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    return FileResponse(path, media_type="text/plain; charset=utf-8", filename=path.name)