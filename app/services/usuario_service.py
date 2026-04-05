from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.models.usuarios import Usuario
from fastapi import UploadFile
from pathlib import Path
import os
from pwdlib import PasswordHash
from app.core.storage import resolve_storage_url, save_uploaded_file

password_hash = PasswordHash.recommended()


def _get_secret_key() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is required")
    return secret


SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8080").rstrip("/")
ALLOWED_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + expires_delta
    payload.update({"exp": expire, "type": token_type})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(data: dict) -> str:
    return _create_token(
        data,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )

def create_refresh_token(data: dict) -> str:
    return _create_token(
        data,
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )

def create_token(data: dict):
    # Compatibilidad hacia atrás con llamadas existentes.
    return create_access_token(data)

def create_token_pair(data: dict) -> tuple[str, str]:
    return create_access_token(data), create_refresh_token(data)

def verify_access_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if token_type not in (None, "access"):
        raise JWTError("Invalid token type")
    return payload

def verify_refresh_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload

def verify_token(token: str) -> dict:
    """
    Decodifica y valida JWT. Lanza excepción si token es inválido o expirado.
    Retorna el payload (ej. {"sub": "username", "exp": timestamp})
    
    Raises:
        JWTError: Si token es inválido, expirado o formato incorrecto
    """
    try:
        return verify_access_token(token)
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


def _to_public_image_url(path: str | None) -> str | None:
    if not path:
        return path

    resolved = resolve_storage_url(path)
    if not resolved:
        return path

    if resolved.startswith("/uploads/"):
        return f"{BACKEND_PUBLIC_URL}{resolved}"

    marker = "/uploads/"
    if marker in resolved:
        return f"{BACKEND_PUBLIC_URL}{resolved[resolved.index(marker):]}"

    return resolved


def save_profile_photo(file: UploadFile) -> str:
    if not file.filename:
        raise ValueError("Archivo vacío")

    try:
        public_image_url = save_uploaded_file(
            file_obj=file.file,
            original_filename=file.filename,
            folder="usuarios",
            allowed_extensions=ALLOWED_IMG_EXTENSIONS,
            content_type=file.content_type,
        )
    except Exception as e:
        raise RuntimeError(f"Error guardando foto: {str(e)}")

    return _to_public_image_url(public_image_url)


def create_usuario_service_with_photo(db, usuario, photo_file: UploadFile | None = None):
    hashed_password = hash_password(usuario.password)
    photo_url = None

    if photo_file is not None and photo_file.filename:
        photo_url = save_profile_photo(photo_file)

    db_usuario = Usuario(
        nombre=usuario.nombre,
        username=usuario.username,
        password_hash=hashed_password,
        foto_url=photo_url,
    )
    try:
        db.add(db_usuario)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(db_usuario)
    return db_usuario


def update_usuario_profile(
    db,
    usuario: Usuario,
    nombre: str | None = None,
    username: str | None = None,
    photo_file: UploadFile | None = None,
):
    changed = False

    if nombre is not None:
        usuario.nombre = nombre
        changed = True

    if username is not None and username != usuario.username:
        existing = db.query(Usuario).filter(Usuario.username == username, Usuario.id != usuario.id).first()
        if existing:
            raise ValueError("Username ya existe")
        usuario.username = username
        changed = True

    if photo_file is not None and photo_file.filename:
        usuario.foto_url = save_profile_photo(photo_file)
        changed = True

    if changed:
        try:
            db.add(usuario)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        db.refresh(usuario)

    usuario.foto_url = _to_public_image_url(usuario.foto_url)
    return usuario


def change_password_service(db, usuario: Usuario, current_password: str, new_password: str):
    if not verify_password(current_password, usuario.password_hash):
        raise ValueError("Contraseña actual incorrecta")

    if verify_password(new_password, usuario.password_hash):
        raise ValueError("La nueva contraseña debe ser distinta a la actual")

    usuario.password_hash = hash_password(new_password)

    try:
        db.add(usuario)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    db.refresh(usuario)
    return usuario