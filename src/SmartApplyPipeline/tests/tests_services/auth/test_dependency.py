import pytest
from fastapi import HTTPException
from app.services.auth.dependency import get_current_user
from app.models.user import User

# On définit un utilisateur de test
MOCK_USER = User(
    google_id="google_123",
    email="test@gmail.com",
    name="Test User",
    access_token="abc",
    refresh_token="def",
    token_expiry=12345
)

@pytest.mark.asyncio
async def test_get_current_user_success(monkeypatch):
    """Cas nominal : Cookie présent, JWT valide et User trouvé."""
    
    # 1. Mock de decode_jwt pour renvoyer le google_id
    monkeypatch.setattr("app.services.auth.dependency.decode_jwt", lambda x: "google_123")
    
    # 2. Mock du UserRepository pour renvoyer notre MOCK_USER
    class MockRepo:
        def find_by_google_id(self, gid): return MOCK_USER
        
    monkeypatch.setattr("app.services.auth.dependency.UserRepository", MockRepo)

    # 3. Appel de la fonction avec un faux cookie
    result = await get_current_user(session="fake_token")

    assert result == MOCK_USER
    assert result.google_id == "google_123"

@pytest.mark.asyncio
async def test_get_current_user_no_cookie():
    """Vérifie l'erreur 401 si le cookie est absent."""
    with pytest.raises(HTTPException) as exc:
        await get_current_user(session=None)
    
    assert exc.value.status_code == 401
    assert "Non authentifié" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_invalid_jwt(monkeypatch):
    """Vérifie l'erreur 401 si le JWT est corrompu ou expiré."""
    
    # Mock qui simule un échec de décodage (renvoie None)
    monkeypatch.setattr("app.services.auth.dependency.decode_jwt", lambda x: None)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(session="invalid_token")
    
    assert exc.value.status_code == 401
    assert "Session invalide" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_not_in_db(monkeypatch):
    """Vérifie l'erreur 401 si le JWT est OK mais l'user a été supprimé de la DB."""
    
    monkeypatch.setattr("app.services.auth.dependency.decode_jwt", lambda x: "unknown_id")
    
    class EmptyRepo:
        def find_by_google_id(self, gid): return None
        
    monkeypatch.setattr("app.services.auth.dependency.UserRepository", EmptyRepo)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(session="valid_token")
    
    assert exc.value.status_code == 401
    assert "Utilisateur introuvable" in exc.value.detail