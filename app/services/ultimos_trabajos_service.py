from fastapi import UploadFile
from sqlmodel import Session, select
import shutil
from pathlib import Path
import os
from uuid import uuid4
from app.models.ultimos_trabajos import UltimosTrabajos
from app.schemas.ultimos_trabajos_schema import *
from app.core.storage import get_uploads_root, is_local_storage

"""
UltimosTrabajos Service
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

def _save_image(file: UploadFile) -> str:
    if not is_local_storage():
        raise RuntimeError("Carga de archivos con STORAGE_BACKEND=s3 aun no implementada")

    file_ext = Path(file.filename).suffix.lower() if file.filename else ""

    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Extensión no permitida. Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    upload_dir = get_uploads_root() / "ultimos_trabajos"
    upload_dir.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    public_image_url = f"/uploads/ultimos_trabajos/{unique_filename}"

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return _to_public_image_url(public_image_url)


def create_ultimo_trabajo(db: Session, titulo: str, descripcion: str, imagenes: list[UploadFile], comentarios: Optional[str] = None):
    imagen_dicts = []
    for imagen in imagenes:
        try:
            url = _save_image(imagen)
            imagen_dicts.append({
                "url": url,
                "nombre": imagen.filename or "imagen"
            })
        except ValueError as e:
            print(f"Error al guardar la imagen {imagen.filename}: {e}")

    nuevo_trabajo = UltimosTrabajos(
        titulo=titulo,
        descripcion=descripcion,
        imagenes=imagen_dicts,
        comentarios=comentarios
    )
    try:
        db.add(nuevo_trabajo)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(nuevo_trabajo)
    return nuevo_trabajo

def get_ultimos_trabajos_active(db: Session):
    trabajos = db.exec(select(UltimosTrabajos).where(UltimosTrabajos.is_active == True).order_by(UltimosTrabajos.created_at.desc())).all()
    for trabajo in trabajos:
        if trabajo.imagenes:
            trabajo.imagenes = [{
                **img,
                "url": _to_public_image_url(img.get("url", ""))
            } for img in trabajo.imagenes]
    return trabajos

def get_ultimo_trabajo_by_id(db: Session, trabajo_id: int):
    trabajo = db.get(UltimosTrabajos, trabajo_id)
    if trabajo and trabajo.imagenes:
        trabajo.imagenes = [{
            **img,
            "url": _to_public_image_url(img.get("url", ""))
        } for img in trabajo.imagenes]
    return trabajo

def get_ultimos_trabajos_all(db: Session):
    trabajos = db.exec(select(UltimosTrabajos).order_by(UltimosTrabajos.created_at.desc())).all()
    for trabajo in trabajos:
        if trabajo.imagenes:
            trabajo.imagenes = [{
                **img,
                "url": _to_public_image_url(img.get("url", ""))
            } for img in trabajo.imagenes]
    return trabajos

def update_ultimo_trabajo(
    db: Session,
    ul_trabajo_id: int,
    titulo: Optional[str] = None,
    descripcion: Optional[str] = None,
    comentarios: Optional[str] = None,
    imagenes: Optional[list[UploadFile]] = None
):
    trabajo = db.get(UltimosTrabajos, ul_trabajo_id)
    if not trabajo:
        return None
    
    # Actualizar campos de texto
    if titulo is not None:
        trabajo.titulo = titulo
    if descripcion is not None:
        trabajo.descripcion = descripcion
    if comentarios is not None:
        trabajo.comentarios = comentarios
    
    # Procesar imágenes si vienen
    if imagenes:
        imagen_dicts = []
        for imagen in imagenes:
            try:
                url = _save_image(imagen)
                imagen_dicts.append({
                    "url": url,
                    "nombre": imagen.filename or "imagen"
                })
            except ValueError as e:
                print(f"Error al guardar la imagen {imagen.filename}: {e}")
        trabajo.imagenes = imagen_dicts
    
    try:
        db.add(trabajo)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(trabajo)
    return trabajo

def deactivate_ultimo_trabajo(db: Session, ul_trabajo_id: int):
    trabajo = db.get(UltimosTrabajos, ul_trabajo_id)
    if not trabajo:
        return None
    trabajo.is_active = False
    try:
        db.add(trabajo)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(trabajo)
    return trabajo

def activate_ultimo_trabajo(db: Session, ul_trabajo_id: int):
    trabajo = db.get(UltimosTrabajos, ul_trabajo_id)
    if not trabajo:
        return None
    trabajo.is_active = True
    try:
        db.add(trabajo)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(trabajo)
    return trabajo

def enviar_encuesta_ultimo_trabajo(
    db: Session,
    ul_trabajo_id: int,
    puntuacion: int,
    comentarios: str,
):
    trabajo = db.get(UltimosTrabajos, ul_trabajo_id)
    if not trabajo:
        return None

    trabajo.puntuacion = puntuacion
    trabajo.comentarios = comentarios.strip()

    try:
        db.add(trabajo)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    db.refresh(trabajo)
    if trabajo.imagenes:
        trabajo.imagenes = [
            {**img, "url": _to_public_image_url(img.get("url", ""))}
            for img in trabajo.imagenes
        ]
    return trabajo


