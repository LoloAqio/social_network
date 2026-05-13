from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id), 
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)  
        }
    token = jwt.encode(payload, settings.secret_key, settings.algorithm)
    return token

def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key,  algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, ValueError):
        return None