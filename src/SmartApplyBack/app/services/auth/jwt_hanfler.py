import os
from datetime import datetime, timedelta
from jose import jwt, JWTError    # pip install python-jose[cryptography]

SECRET_KEY = os.getenv("JWT_SECRET_KEY")   # à mettre dans .env !
ALGORITHM  = "HS256"
EXPIRE_DAYS = 7


def create_jwt(google_id: str) -> str:
    payload = {
        "sub": google_id,
        "exp": datetime.utcnow() + timedelta(days=EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")   # google_id
    except JWTError:
        return None