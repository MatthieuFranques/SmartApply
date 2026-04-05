import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.services.auth.jwt_handler import create_jwt, decode_jwt, SECRET_KEY, ALGORITHM

def test_create_and_decode_jwt_success():
    """Vérifie qu'un token créé peut être décodé correctement."""
    google_id = "test_user_123"
    
    # 1. Création
    token = create_jwt(google_id)
    assert isinstance(token, str)
    
    # 2. Décodage
    decoded_id = decode_jwt(token)
    assert decoded_id == google_id

def test_decode_jwt_invalid_token():
    """Vérifie que le décodage échoue avec un token malformé."""
    invalid_token = "not.a.real.token"
    assert decode_jwt(invalid_token) is None

def test_decode_jwt_expired_token(monkeypatch):
    """Vérifie que le décodage échoue si le token est expiré."""
    google_id = "expired_user"
    
    # On crée un payload déjà expiré manuellement pour le test
    payload = {
        "sub": google_id,
        "exp": datetime.utcnow() - timedelta(minutes=1) # Expire il y a 1 min
    }
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    assert decode_jwt(expired_token) is None

def test_decode_jwt_wrong_secret():
    """Vérifie que le décodage échoue si la clé secrète est différente."""
    google_id = "secret_user"
    wrong_secret = "another_very_secret_key"
    
    payload = {
        "sub": google_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token_with_wrong_secret = jwt.encode(payload, wrong_secret, algorithm=ALGORITHM)
    
    assert decode_jwt(token_with_wrong_secret) is None

def test_decode_jwt_missing_sub():
    """Vérifie que le décodage renvoie None si 'sub' est absent du payload."""
    payload = {
        "exp": datetime.utcnow() + timedelta(hours=1)
        # Manque le "sub"
    }
    token_no_sub = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    assert decode_jwt(token_no_sub) is None