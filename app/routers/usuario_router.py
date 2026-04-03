from fastapi  import APIRouter, Depends, HTTPException, status, Header, Response, Cookie
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.services.usuario_service import *
from app.schemas.usuario_schema import *
from app.models.usuarios import Usuario
from jose import JWTError
import os

usuario_router = APIRouter(prefix="/users", tags=["usuarios"])


async def get_current_user_optional(
    authorization: str = Header(None),
    mb_access_token: str | None = Cookie(None),
    db: Session = Depends(get_session)
) -> Usuario | None:
    """
    Dependency opcional que valida JWT si está presente.
    Lee desde: 1) Cookie mb_access_token, 2) Authorization header
    Retorna Usuario si token válido, None si no hay token.
    """
    token = mb_access_token
    
    if not token and authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                token = None
        except:
            token = None
    
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    
    user = db.query(Usuario).filter(Usuario.username == username).first()
    return user


async def get_current_user(
    authorization: str = Header(None),
    mb_access_token: str | None = Cookie(None),
    db: Session = Depends(get_session)
) -> Usuario:
    """
    Dependency que valida JWT. Lee desde:
    1. Cookie mb_access_token (primera opción)
    2. Authorization header (fallback para backend-to-backend)
    
    Raises:
        HTTPException 401: Si no hay token, es inválido o está expirado
        HTTPException 404: Si el usuario no existe en BD
    """
    token = mb_access_token  # Cookie tiene prioridad
    
    if not token and authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                token = None
        except:
            token = None
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar token
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if not username:
            raise ValueError("No username in token")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener usuario de BD
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@usuario_router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, response: Response, db: Session = Depends(get_session)):
    user = db.query(Usuario).filter(Usuario.username == datos.username).first()
    if not user or not verify_password(datos.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token_data = {"sub": user.username}
    access_token = create_token(token_data)
    
    # Setear cookie httpOnly
    is_secure = os.getenv("ENVIRONMENT") == "production"
    response.set_cookie(
        key="mb_access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,  # False en local, True en prod
        samesite="lax",
        max_age=86400  # 24 horas
    )
    
    return LoginResponse(access_token=access_token, token_type="bearer")

@usuario_router.post("/logout")
def logout(response: Response):
    """
    Endpoint para logout. Borra el cookie httpOnly del navegador.
    Puede ser llamado sin autenticación (para logout después de sesión expirada).
    """
    response.delete_cookie(
        key="mb_access_token",
        path="/",
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax"
    )
    return {"message": "Logged out successfully"}

@usuario_router.post("/create", response_model=UsuarioRead)
def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_session),
    current_user: Usuario | None = Depends(get_current_user_optional)
):
    # Permitir crear primer usuario sin autenticación
    # Si hay usuarios en la BD, requiere autenticación
    user_count = db.query(Usuario).count()
    if user_count > 0 and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to create additional users",
        )
    return create_usuario_service(db, usuario)

@usuario_router.get("/verify", response_model=UsuarioRead)
async def verify_token_router(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para verificar que el JWT es válido y retorna los datos del usuario.
    Usado en frontend para revalidar sesión al montar.
    Requiere Authorization header con Bearer token.
    """
    return current_user


