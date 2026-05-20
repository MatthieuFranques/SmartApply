import datetime
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.models.letter import (
    DEFAULT_MODEL,
    INPUT_FILE,
    OUTPUT_DIR,
    CompanySearchRequest,
    GenerateRequest,
    GenerateResponse,
)
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.repositories.profile_repository import UserProfileRepository
from app.services.auth.dependency import get_current_user
from app.services.generate_letter.generate_letter_generator import (
    check_rag,
    determine_mode,
    generate_contact_form,
    generate_letter,
)

router = APIRouter(prefix="/letter", tags=["letter"])

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _find_company(name: str, input_file: str | None) -> dict:
    resolved_file = Path(input_file) if input_file else INPUT_FILE
    if not resolved_file.exists():
        parent = resolved_file.parent
        files = [f.name for f in parent.glob("*")] if parent.exists() else []
        raise HTTPException(
            status_code=404,
            detail={"error": "Fichier introuvable", "path": str(resolved_file), "files": files},
        )
    try:
        companies = json.loads(resolved_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erreur lecture JSON : {e}")

    matches = [c for c in companies if name.lower() in c.get("nom", "").lower()]
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"Entreprise '{name}' non trouvée. Exemples : {[c.get('nom') for c in companies[:5]]}",
        )
    if len(matches) > 1:
        raise HTTPException(status_code=409, detail="Plusieurs entreprises correspondent.")
    return matches[0]


def _find_generated_file(name: str, output_dir: Path) -> Path:
    slug = name.lower().replace(" ", "_")
    candidates = list(output_dir.glob(f"{slug}*.txt")) + list(output_dir.glob(f"{slug}*.json"))
    if not candidates:
        raise HTTPException(status_code=404, detail=f"Aucun fichier pour '{name}'.")
    return max(candidates, key=lambda p: p.stat().st_mtime)


@router.post("/", response_model=GenerateResponse, status_code=201)
def generate(body: GenerateRequest):
    if not check_rag():
        raise HTTPException(status_code=503, detail="Service RAG inaccessible.")

    company    = _find_company(body.name, body.input_file)
    output_dir = Path(body.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mode       = determine_mode(company)

    safe_name = "".join(x for x in company["nom"] if x.isalnum() or x in "._- ")
    filepath  = output_dir / f"{safe_name}.json"

    try:
        if mode == "contact":
            content    = generate_contact_form(company, body.model)
            mode_label = "contact"
        else:
            content    = generate_letter(company, body.model)
            mode_label = "letter_targeted" if company.get("job_offers") else "letter_spontaneous"

        filepath.write_text(
            json.dumps(
                {
                    "company":  company["nom"],
                    "date":     datetime.date.today().isoformat(),
                    "mode":     mode_label,
                    "model":    body.model,
                    "content":  content,
                    "metadata": {"domaine": company.get("domaine"), "ville": company.get("ville")},
                },
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return GenerateResponse(
        company=company["nom"],
        filename=filepath.name,
        mode=mode_label,
        model=body.model,
        output_dir=str(output_dir),
    )


@router.get("/{name}")
def generate_letter_for_company(
    name: str,
    model: str = Query(default=DEFAULT_MODEL),
    current_user: User = Depends(get_current_user),
):
    if not check_rag():
        raise HTTPException(status_code=503, detail="Service RAG inaccessible")

    repo    = JobRepository()
    decoded = name.replace("%20", " ")
    job     = next(
        (j for j in repo.find_by_user(current_user.google_id) if j.nom.lower() == decoded.lower()),
        None,
    )
    if not job:
        raise HTTPException(status_code=404, detail=f"Entreprise '{decoded}' introuvable")

    profile_repo     = UserProfileRepository()
    user_profile     = profile_repo.get(current_user.google_id)
    reference_letter = user_profile.pop("reference_letter", "")
    user_profile.pop("cv_text", None)

    job_dict = job.model_dump(mode="json")
    mode = determine_mode(job_dict)

    try:
        if mode == "contact":
            result = generate_contact_form(job_dict, model, user_profile, current_user.google_id)
            return {"letter": None, "contact_form": result, "mode": "contact"}
        else:
            letter_text = generate_letter(job_dict, model, user_profile, reference_letter, current_user.google_id)
            return {"letter": letter_text, "mode": "letter"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG indisponible : {e}")


@router.get("/details")
def get_letter_by_body(
    request: CompanySearchRequest,
    output_dir: str = Query(default=str(OUTPUT_DIR)),
):
    path = _find_generated_file(request.name, Path(output_dir))
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return FileResponse(path, media_type="text/plain; charset=utf-8", filename=path.name)
