from fastapi import UploadFile
from sqlmodel import Session, select
import os
from app.models.ultimos_trabajos import UltimosTrabajos
from app.schemas.ultimos_trabajos_schema import *
from app.core.storage import resolve_storage_url, save_uploaded_file

"""
UltimosTrabajos Service
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

def _save_image(file: UploadFile) -> str:
    public_image_url = save_uploaded_file(
        file_obj=file.file,
        original_filename=file.filename,
        folder="ultimos_trabajos",
        allowed_extensions=ALLOWED_EXTENSIONS,
        content_type=file.content_type,
    )

    return public_image_url


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


