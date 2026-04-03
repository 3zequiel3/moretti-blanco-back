from fastapi import UploadFile
from sqlmodel import Session, select
from app.models.carrousel import Carrousel
from app.schemas.carrousel_schema import *
import shutil
from pathlib import Path
import os
from uuid import uuid4
from app.core.storage import get_uploads_root, is_local_storage


"""
Carrousel Service
"""


BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8080").rstrip("/")


def _to_public_image_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path

    if path.startswith("/uploads/"):
        return f"{BACKEND_PUBLIC_URL}{path}"

    marker = "/uploads/"
    if marker in path:
        return f"{BACKEND_PUBLIC_URL}{path[path.index(marker):]}"

    return path


"""
Crear un nuevo slice del carrousel
"""
def create_carrousel(db:Session, descripcion:str, orden:int, file:UploadFile):
    if not is_local_storage():
        raise RuntimeError("Carga de archivos con STORAGE_BACKEND=s3 aun no implementada")

    # Validar extensión de archivo permitida
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensión no permitida. Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}")
    
    upload_dir = get_uploads_root() / "carrousel"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre único para evitar sobrescrituras
    unique_filename = f"{uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    public_image_url = f"/uploads/carrousel/{unique_filename}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        db.rollback()
        raise e
    
    new_carrousel = Carrousel(
        image_url=_to_public_image_url(public_image_url),
        descripcion=descripcion,
        orden=orden,
    )
    try:
        db.add(new_carrousel)
        db.commit()
    except Exception as e:
        db.rollback()
        if file_path.exists():
            os.remove(file_path)
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