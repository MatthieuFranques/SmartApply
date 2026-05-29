"""Smoke tests for RAG request/response schemas."""

from app.models import schemas


def test_index_schemas_defaults():
    assert schemas.IndexLetterRequest(letter_text="t", company={}, mode="letter").user_id == "default"
    assert schemas.IndexCVRequest(profile={}).user_id == "default"
    assert schemas.IndexReferenceRequest(letter_text="t", source="s").company_type == "generic"
    resp = schemas.IndexResponse(success=True, doc_ids=["a"], collection="letters")
    assert resp.success is True


def test_retrieve_schemas_defaults():
    req = schemas.RetrieveContextRequest(company={})
    assert (req.k_letters, req.k_cv, req.k_refs) == (3, 3, 2)
    assert schemas.RetrieveContextResponse().has_context is False


def test_generate_schemas_defaults():
    assert schemas.GenerateLetterRequest(company={}, profile={}).reference_letter == ""
    resp = schemas.GenerateLetterResponse(letter="l", mode="m", model="mistral")
    assert resp.letter == "l"
    assert schemas.GenerateContactRequest(company={}, profile={}).user_id == "default"
