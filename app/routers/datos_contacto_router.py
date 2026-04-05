import json
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.services.datos_contacto_service import *
from app.schemas.datos_contacto_schema import *
from app.models.datos_contacto import DatosContacto
from app.models.usuarios import Usuario
from app.routers.usuario_router import get_current_user

datos_contacto_router = APIRouter(prefix="/contacto", tags=["contacto"])


def _parse_links_botones(raw_links: str) -> dict[str, str]:
    if not raw_links:
        return {}

    try:
        parsed = json.loads(raw_links)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="Formato de links_botones invalido. Debe ser JSON.",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=422,
            detail="links_botones debe ser un objeto JSON clave/valor.",
        )

    sanitized: dict[str, str] = {}
    for key, value in parsed.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise HTTPException(
                status_code=422,
                detail="links_botones solo acepta claves y valores string.",
            )
        sanitized[key] = value

    return sanitized

@datos_contacto_router.get("/" ,response_model=Optional[DatosContactoRead])
async def get_all_contact_data_router(
    db: Session = Depends(get_session)
):
    # GET público: Sin autenticación requerida (para la página pública)
    contact_data = get_contact_data(db)
    return contact_data


@datos_contacto_router.get("/list", response_model=list[DatosContactoRead])
async def get_contact_data_list_router(
    db: Session = Depends(get_session)
):
    # GET publico: habilita render de multiples cards en la vista cliente.
    return get_contact_data_list(db)

@datos_contacto_router.post("/", response_model=DatosContactoRead)
async def create_contact_data_router(
    db: Session = Depends(get_session),
    nombre: str = Form(...),
    cargo: str = Form(""),
    telefono: str = Form(...),
    file: UploadFile = File(...),
    links_botones: str = Form(...),
    current_user: Usuario = Depends(get_current_user)
):
    links_botones_dict = _parse_links_botones(links_botones)

    try:
        return create_contact_data(
            db,
            nombre,
            cargo.strip() or None,
            telefono,
            file,
            links_botones_dict,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@datos_contacto_router.patch("/{contact_data_id}", response_model=DatosContactoRead)
async def update_contact_data_router(
    contact_data_id: int,
    data: DatosContactoUpdate,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return update_contact_data(db, contact_data_id, data)
    except Exception as exc:
        if "no encontrados" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=500, detail="Error al actualizar datos de contacto") from exc

@datos_contacto_router.post("/{contact_data_id}/update_photo", response_model=DatosContactoRead)
async def update_contact_data_photo_router(
    contact_data_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return update_contact_data_photo(db, contact_data_id, file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        if "no encontrados" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=500, detail="Error al actualizar la foto de contacto") from exc