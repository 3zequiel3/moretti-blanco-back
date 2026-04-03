from sqlmodel import SQLModel
from typing import Optional


class CarrouselCreate(SQLModel):
    image_url: str
    descripcion: str
    orden: int

class CarrouselRead(SQLModel):
    id: int
    image_url: str
    descripcion: str
    orden: int
    is_active: bool

class CarrouselUpdate(SQLModel):
    image_url: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    is_active: Optional[bool] = None

class CarrouselActive(SQLModel):
    is_active: bool
