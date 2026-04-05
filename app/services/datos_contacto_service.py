from fastapi import UploadFile
from sqlmodel import Session, select
import os
from app.models.datos_contacto import DatosContacto
from app.schemas.datos_contacto_schema import *
from app.core.storage import resolve_storage_url, save_uploaded_file


"""
DatosContacto Service
"""


BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8080").rstrip("/")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def _to_public_image_url(path: str) -> str:
    resolved = resolve_storage_url(path)
    if not resolved:
        return path

    if resolved.startswith("http://") or resolved.startswith("https://"):
        return resolved

    if resolved.startswith("/uploads/"):
        return f"{BACKEND_PUBLIC_URL}{resolved}"

    marker = "/uploads/"
    if marker in resolved:
        return f"{BACKEND_PUBLIC_URL}{resolved[resolved.index(marker):]}"

    return resolved


def _save_contact_photo(file: UploadFile) -> str:
    public_image_url = save_uploaded_file(
        file_obj=file.file,
        original_filename=file.filename,
        folder="contacto",
        allowed_extensions=ALLOWED_EXTENSIONS,
        content_type=file.content_type,
    )

    return public_image_url

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