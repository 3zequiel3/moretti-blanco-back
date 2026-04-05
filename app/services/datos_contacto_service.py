from fastapi import UploadFile
from sqlmodel import Session, select
import shutil
from pathlib import Path
import os
from uuid import uuid4
from app.models.datos_contacto import DatosContacto
from app.schemas.datos_contacto_schema import *
from app.core.storage import get_uploads_root, is_local_storage


"""
DatosContacto Service
"""


BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8080").rstrip("/")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def _to_public_image_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path

    if path.startswith("/uploads/"):
        return f"{BACKEND_PUBLIC_URL}{path}"

    marker = "/uploads/"
    if marker in path:
        return f"{BACKEND_PUBLIC_URL}{path[path.index(marker):]}"

    return path


def _save_contact_photo(file: UploadFile) -> str:
    if not is_local_storage():
        raise RuntimeError("Carga de archivos con STORAGE_BACKEND=s3 aun no implementada")

    file_ext = Path(file.filename).suffix.lower() if file.filename else ""

    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Extensión no permitida. Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    upload_dir = get_uploads_root() / "contacto"
    upload_dir.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    public_image_url = f"/uploads/contacto/{unique_filename}"

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return _to_public_image_url(public_image_url)

def create_contact_data(
    db: Session,
    nombre: str,
    cargo: str | None,
    telefono: str,
    file: UploadFile,
    links_botones: dict,
):
    public_image_url = _save_contact_photo(file)

    new_contact_data = DatosContacto(
        nombre=nombre,
        cargo=cargo,
        telefono=telefono,
        foto_url=public_image_url,
        links_botones=links_botones
    )
    try:
        db.add(new_contact_data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_contact_data)
    return new_contact_data

def get_contact_data(db: Session):
    contact_data = db.exec(select(DatosContacto)).first()
    if contact_data and contact_data.foto_url:
        contact_data.foto_url = _to_public_image_url(contact_data.foto_url)
    return contact_data


def get_contact_data_list(db: Session):
    contact_data_list = db.exec(select(DatosContacto).order_by(DatosContacto.id)).all()
    normalized: list[DatosContacto] = []

    for contact in contact_data_list:
        if contact.foto_url:
            contact.foto_url = _to_public_image_url(contact.foto_url)
        normalized.append(contact)

    return normalized

def update_contact_data(db: Session, contact_data_id: int, data: DatosContactoUpdate):
    contact_data = db.get(DatosContacto, contact_data_id)
    if not contact_data:
        raise Exception("Datos de contacto no encontrados")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contact_data, key, value)
    try:
        db.add(contact_data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(contact_data)
    return contact_data

def update_contact_data_photo(db: Session, contact_data_id: int, file: UploadFile):
    """Actualiza exclusivamente la foto de contacto a partir de un archivo."""
    contact_data = db.get(DatosContacto, contact_data_id)
    if not contact_data:
        raise Exception("Datos de contacto no encontrados")

    try:
        contact_data.foto_url = _save_contact_photo(file)
        db.add(contact_data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(contact_data)
    return contact_data


def update_contact_data_photo_url(db: Session, contact_data_id: int, data: DatosContactoUpdateFoto):
    """Compatibilidad temporal: actualiza foto_url directamente cuando llega como string."""
    contact_data = db.get(DatosContacto, contact_data_id)
    if not contact_data:
        raise Exception("Datos de contacto no encontrados")
    contact_data.foto_url = _to_public_image_url(data.foto_url)
    try:
        db.add(contact_data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(contact_data)
    return contact_data