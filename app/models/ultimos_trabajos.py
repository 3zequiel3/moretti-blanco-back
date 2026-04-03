from datetime import datetime

from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Column, JSON, DateTime, func


class UltimosTrabajos(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    descripcion: str
    imagenes: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    comentarios: Optional[str] = None
    is_active: bool = Field(default=True)
    puntuacion: int = Field(default=1, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False, server_default=func.now()))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now()))