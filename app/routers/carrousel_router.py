from fastapi import APIRouter, Depends, File, UploadFile, Form, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.services.carrousel_service import *
from app.schemas.carrousel_schema import *
from app.models.carrousel import Carrousel
from app.models.usuarios import Usuario
from app.routers.usuario_router import get_current_user

carrousel_router = APIRouter(prefix="/carrousel", tags=["carrousel"])



@carrousel_router.get("" ,response_model=list[CarrouselRead])
async def get_all_carrousels_router(
    db: Session = Depends(get_session)
):
    # GET público: Sin autenticación requerida (para la página pública)
    return get_all_carrousels(db)



@carrousel_router.get("/{carrousel_id}", response_model=CarrouselRead)
async def get_carrousel_router(
    carrousel_id: int,
    db: Session = Depends(get_session)
):
    # GET público: Sin autenticación requerida (para la página pública)
    try:
        return get_carrousel_by_id(db, carrousel_id)
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Carrousel no encontrado") from exc
        raise HTTPException(status_code=500, detail="Error al obtener el carrousel") from exc



@carrousel_router.post("", response_model=CarrouselRead)
async def create_carrousel_router( 
    descripcion: str = Form(...),
    orden: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return create_carrousel(db, descripcion, orden, file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error al crear el carrousel") from exc



@carrousel_router.patch("/{carrousel_id}", response_model=CarrouselRead)
async def update_carrousel_router(
    carrousel_id: int,
    data: CarrouselUpdate,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return update_carrousel(db, carrousel_id, data)
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Carrousel no encontrado") from exc
        raise HTTPException(status_code=500, detail="Error al actualizar el carrousel") from exc



@carrousel_router.post("/{carrousel_id}/deactivate")
async def deactivate_carrousel_router(
    carrousel_id: int,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        deactivate(db, carrousel_id)
        return {"message": "Carrousel desactivado exitosamente"}
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Carrousel no encontrado") from exc
        raise HTTPException(status_code=500, detail="Error al desactivar el carrousel") from exc



@carrousel_router.post("/{carrousel_id}/activate")
async def activate_carrousel_router(
    carrousel_id: int,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        activate(db, carrousel_id)
        return {"message": "Carrousel activado exitosamente"}
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Carrousel no encontrado") from exc
        raise HTTPException(status_code=500, detail="Error al activar el carrousel") from exc