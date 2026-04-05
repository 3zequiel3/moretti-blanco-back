from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Column, JSON

class DatosContacto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    cargo: Optional[str] = None
    telefono: str
    foto_url: Optional[str] = None
    links_botones: dict = Field(default_factory=dict, sa_column=Column(JSON))