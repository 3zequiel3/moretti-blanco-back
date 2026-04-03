from sqlmodel import SQLModel, Field
from typing import Optional

class Carrousel(SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_url: str
    descripcion: str
    orden: int
    is_active: bool = Field(default=True)
    