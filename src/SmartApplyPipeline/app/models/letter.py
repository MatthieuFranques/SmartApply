from pathlib import Path
from pydantic import BaseModel
from typing import Optional

# On récupère le chemin du dossier 'app' (parent de 'models')
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
# On définit les chemins ABSOLUS
# Si ton fichier est dans app/results/enriched.json
INPUT_FILE = ROOT_DIR / "results" / "enriched.json"
OUTPUT_DIR = ROOT_DIR / "letters"

DEFAULT_MODEL = "mistral"

class CompanySearchRequest(BaseModel):
    name: str
    
class GenerateRequest(BaseModel):
    name: str
    model: Optional[str] = DEFAULT_MODEL
    input_file: Optional[str] = str(INPUT_FILE)
    output_dir: Optional[str] = str(OUTPUT_DIR)

class GenerateResponse(BaseModel):
    company:    str
    filename:   str
    mode:       str
    model:      str
    output_dir: str

class LetterItem(BaseModel):
    filename: str
    size_kb:  float
    path:     str