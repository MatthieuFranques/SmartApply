from fastapi import APIRouter, HTTPException

from app.models.schemas import GenerateLetterRequest, GenerateLetterResponse, GenerateContactRequest
from app.services.generator import determine_mode, generate_contact_form, generate_letter

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/letter", response_model=GenerateLetterResponse)
def generate_letter_endpoint(body: GenerateLetterRequest):
    print(f"[RAG /generate/letter] company={body.company.get('nom')} model={body.model}", flush=True)
    try:
        mode = determine_mode(body.company)
        if mode == "contact":
            raise HTTPException(
                status_code=400,
                detail="Entreprise détectée comme formulaire de contact — utilise POST /generate/contact",
            )
        letter = generate_letter(
            company=body.company,
            profile=body.profile,
            model=body.model,
            reference_letter=body.reference_letter,
            user_id=body.user_id,
        )
        print(f"[RAG /generate/letter] SUCCESS len={len(letter)}", flush=True)
        return GenerateLetterResponse(
            letter=letter,
            mode="letter_targeted" if body.company.get("job_offers") else "letter_spontaneous",
            model=body.model,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[RAG /generate/letter] EXCEPTION type={type(e).__name__} msg={e}", flush=True)
        raise HTTPException(status_code=503, detail=f"Génération échouée : {e}")


@router.post("/contact")
def generate_contact_endpoint(body: GenerateContactRequest):
    print(f"[RAG /generate/contact] company={body.company.get('nom')} model={body.model}", flush=True)
    try:
        result = generate_contact_form(
            company=body.company,
            profile=body.profile,
            model=body.model,
            user_id=body.user_id,
        )
        print(f"[RAG /generate/contact] SUCCESS", flush=True)
        return result
    except Exception as e:
        print(f"[RAG /generate/contact] EXCEPTION type={type(e).__name__} msg={e}", flush=True)
        raise HTTPException(status_code=503, detail=f"Génération échouée : {e}")
