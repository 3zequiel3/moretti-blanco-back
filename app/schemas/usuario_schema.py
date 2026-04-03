from sqlmodel import SQLModel, Field
from typing import Optional


class UsuarioCreate(SQLModel):
    nombre: str
    username: str
    password: str = Field(min_length=8, max_length=128)


class UsuarioRead(SQLModel):
    id: int
    nombre: str
    username: str


class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

class LoginRequest(SQLModel):
    username: str
    password: str = Field(min_length=1, max_length=128)

class LoginResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"