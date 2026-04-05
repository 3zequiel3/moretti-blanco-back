from sqlmodel import SQLModel
from typing import Optional
class DatosContactoCreate(SQLModel):
    nombre: str
    cargo: Optional[str] = None
    telefono: str
    foto_url: str
    links_botones: dict

class DatosContactoRead(SQLModel):
    id: int
    nombre: str
    cargo: Optional[str] = None
    telefono: str
    foto_url: Optional[str] = None
    links_botones: dict

class DatosContactoUpdate(SQLModel):
    nombre: Optional[str] = None
    cargo: Optional[str] = None
    telefono: Optional[str] = None
    links_botones: Optional[dict] = None

class DatosContactoUpdateFoto(SQLModel):
    foto_url: str