from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.services.ultimos_trabajos_service import *
from app.schemas.ultimos_trabajos_schema import *
from app.models.ultimos_trabajos import UltimosTrabajos
from app.models.usuarios import Usuario
from app.routers.usuario_router import get_current_user


ultimo_trabajo_router = APIRouter(prefix="/ultimos-trabajos", tags=["ultimos-trabajos"])


@ultimo_trabajo_router.post("", response_model=UltimosTrabajosRead)
async def create_ultimo_trabajo_router(
    db: Session = Depends(get_session),
    titulo: str = Form(...),
    descripcion: str = Form(...),
    imagenes: list[UploadFile] = File(...),
    comentarios: Optional[str] = Form(None),
    puntuacion: Optional[int] = Form(None, ge=1, le=5),
    current_user: Usuario = Depends(get_current_user)
):
    return create_ultimo_trabajo(db, titulo, descripcion, imagenes, comentarios)

@ultimo_trabajo_router.get("/all", response_model=list[UltimosTrabajosRead])
async def get_ultimos_trabajos_all_router(
    db: Session = Depends(get_session)
):
    ultimos_trabajos = get_ultimos_trabajos_all(db)
    if not ultimos_trabajos:
        raise HTTPException(status_code=404, detail="No se encontraron trabajos")
    return ultimos_trabajos

@ultimo_trabajo_router.get("/active", response_model=list[UltimosTrabajosRead])
async def get_ultimos_trabajos_active_router(
    db: Session = Depends(get_session)
):
    ultimos_trabajos = get_ultimos_trabajos_active(db)
    if not ultimos_trabajos:
        raise HTTPException(status_code=404, detail="No se encontraron trabajos activos")
    return ultimos_trabajos

@ultimo_trabajo_router.get("/{trabajo_id}", response_model=UltimosTrabajosRead)
async def get_ultimo_trabajo_by_id_router(
    trabajo_id: int,
    db: Session = Depends(get_session)
):
    trabajo = get_ultimo_trabajo_by_id(db, trabajo_id)
    if not trabajo:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return trabajo

@ultimo_trabajo_router.patch("/{trabajo_id}", response_model=UltimosTrabajosRead)
async def update_ultimo_trabajo_router(
    trabajo_id: int,
    titulo: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    comentarios: Optional[str] = Form(None),
    imagenes: Optional[list[UploadFile]] = File(None),
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    updated_trabajo = update_ultimo_trabajo(db, trabajo_id, titulo, descripcion, comentarios, imagenes)
    if not updated_trabajo:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return updated_trabajo

@ultimo_trabajo_router.post("/{trabajo_id}/activate", response_model=UltimosTrabajosRead)
async def activate_ultimo_trabajo_router(
    trabajo_id: int,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    updated_trabajo = activate_ultimo_trabajo(db, trabajo_id)
    if not updated_trabajo:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return updated_trabajo

@ultimo_trabajo_router.post("/{trabajo_id}/deactivate", response_model=UltimosTrabajosRead)
async def deactivate_ultimo_trabajo_router(
    trabajo_id: int,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    updated_trabajo = deactivate_ultimo_trabajo(db, trabajo_id)
    if not updated_trabajo:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return updated_trabajo

@ultimo_trabajo_router.post("/{trabajo_id}/encuesta", response_model=UltimosTrabajosRead)
async def encuesta_ultimo_trabajo_router(
    trabajo_id: int,
    puntuacion: int = Form(..., ge=1, le=5),
    comentarios: str = Form(..., min_length=3, max_length=1200),
    db: Session = Depends(get_session),
):
    updated_trabajo = enviar_encuesta_ultimo_trabajo(
        db,
        trabajo_id,
        puntuacion,
        comentarios,
    )
    if not updated_trabajo:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return updated_trabajo