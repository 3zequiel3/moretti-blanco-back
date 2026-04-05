from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Column, JSON
from datetime import datetime

class UltimosTrabajosCreate(SQLModel):
    titulo: str
    descripcion: str
    imagenes: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    comentarios: Optional[str] = None

class UltimosTrabajosRead(SQLModel):
    id: int
    titulo: str
    descripcion: str
    imagenes: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    comentarios: Optional[str] = None
    puntuacion: Optional[int] = None
    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime

class UltimosTrabajosUpdate(SQLModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    imagenes: Optional[list[dict]] = None
    comentarios: Optional[str] = None

class UltimosTrabajosUpdateImagenes(SQLModel):
    imagenes: list[dict] = Field(default_factory=list, sa_column=Column(JSON))

class UltimosTrabajosActive(SQLModel):
    is_active: bool = Field(default=True)

class UltimosTrabajosRanking(SQLModel):
    puntuacion: int = Field(default=1, ge=1, le=5)
    comentarios: Optional[str] = None


class UltimosTrabajosEncuesta(SQLModel):
    puntuacion: int = Field(..., ge=1, le=5)
    comentarios: str = Field(..., min_length=3, max_length=1200)