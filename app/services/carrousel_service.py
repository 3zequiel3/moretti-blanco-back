from fastapi import UploadFile
from sqlmodel import Session, select
from app.models.carrousel import Carrousel
from app.schemas.carrousel_schema import *
import os
from app.core.storage import resolve_storage_url, save_uploaded_file


"""
Carrousel Service
"""


BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8080").rstrip("/")


def _to_public_image_url(path: str) -> str:
    resolved = resolve_storage_url(path)
    if not resolved:
        return path

    if resolved.startswith("/uploads/"):
        return f"{BACKEND_PUBLIC_URL}{resolved}"

    marker = "/uploads/"
    if marker in resolved:
        return f"{BACKEND_PUBLIC_URL}{resolved[resolved.index(marker):]}"

    return resolved


"""
Crear un nuevo slice del carrousel
"""
def create_carrousel(db:Session, descripcion:str, orden:int, file:UploadFile):
    # Validar extensión de archivo permitida
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    public_image_url = save_uploaded_file(
        file_obj=file.file,
        original_filename=file.filename,
        folder="carrousel",
        allowed_extensions=ALLOWED_EXTENSIONS,
        content_type=file.content_type,
    )
    
    try:
        normalized_image_url = _to_public_image_url(public_image_url)
    except Exception as e:
        db.rollback()
        raise e
    
    new_carrousel = Carrousel(
        image_url=normalized_image_url,
        descripcion=descripcion,
        orden=orden,
    )
    try:
        db.add(new_carrousel)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_carrousel)
    return new_carrousel
"""
Obtener todos los slices del carrousel
"""
def get_all_carrousels(db:Session):
    carrousels = db.exec(select(Carrousel)).all()
    for carrousel in carrousels:
        carrousel.image_url = _to_public_image_url(carrousel.image_url)
    return carrousels

"""
Obtener un slice del carrousel por su titulo
"""
def get_carrousel_by_id(db:Session, carrousel_id:int):
    carrousel = db.get(Carrousel, carrousel_id)
    if not carrousel:
        raise Exception("Carrousel not found")
    carrousel.image_url = _to_public_image_url(carrousel.image_url)
    return carrousel

"""
Actualizar un slice del carrousel por su id
"""
def update_carrousel(db:Session, carrousel_id:int, data:CarrouselUpdate):
    carrousel = db.get(Carrousel, carrousel_id)
    if not carrousel:
        raise Exception("Carrousel not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "image_url" and value is not None:
            value = _to_public_image_url(value)
        setattr(carrousel, key, value)
    try:
        db.add(carrousel)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(carrousel)
    return carrousel


"""
Desactivar un slice del carrousel por su id
SOFT DELETE
"""

def deactivate(db:Session, carrousel_id:int):
    carrousel = db.get(Carrousel, carrousel_id)
    if not carrousel:
        raise Exception("Carrousel not found")
    try:
        carrousel.is_active = False
        db.add(carrousel)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(carrousel)
    return carrousel

"""
Activar un slice del carrousel por su id
"""
def activate(db:Session, carrousel_id:int):
    carrousel = db.get(Carrousel, carrousel_id)
    if not carrousel:
        raise Exception("Carrousel not found")
    try:
        carrousel.is_active = True
        db.add(carrousel)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(carrousel)
    return carrousel