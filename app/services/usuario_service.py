from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.models.usuarios import Usuario
import os
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def _get_secret_key() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is required")
    return secret


SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_token(data: dict):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """
    Decodifica y valida JWT. Lanza excepción si token es inválido o expirado.
    Retorna el payload (ej. {"sub": "username", "exp": timestamp})
    
    Raises:
        JWTError: Si token es inválido, expirado o formato incorrecto
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid or expired token: {str(e)}")

def create_usuario_service(db, usuario):
    hashed_password = hash_password(usuario.password)
    db_usuario = Usuario(
        nombre=usuario.nombre,
        username=usuario.username,
        password_hash=hashed_password,
    )
    try:
        db.add(db_usuario)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(db_usuario)
    return db_usuario