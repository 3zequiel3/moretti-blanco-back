from fastapi  import APIRouter, Depends, HTTPException, status, Header, Response, Cookie, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.services.usuario_service import *
from app.services.usuario_service import _to_public_image_url
from app.schemas.usuario_schema import *
from app.models.usuarios import Usuario
from jose import JWTError
import os

usuario_router = APIRouter(prefix="/users", tags=["usuarios"])
ACCESS_COOKIE_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


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
        payload = verify_access_token(token)
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
        payload = verify_access_token(token)
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
    access_token, refresh_token = create_token_pair(token_data)
    
    # Setear cookie httpOnly
    is_secure = os.getenv("ENVIRONMENT") == "production"
    response.set_cookie(
        key="mb_access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,  # False en local, True en prod
        samesite="lax",
        path="/",
        max_age=ACCESS_COOKIE_MAX_AGE,
    )
    response.set_cookie(
        key="mb_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_COOKIE_MAX_AGE,
    )

@usuario_router.post("/refresh", response_model=LoginResponse)
def refresh_session(
    response: Response,
    mb_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_session),
):
    if not mb_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    try:
        payload = verify_refresh_token(mb_refresh_token)
        username: str = payload.get("sub")
        if not username:
            raise ValueError("No username in token")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    token_data = {"sub": user.username}
    access_token, refresh_token = create_token_pair(token_data)
    is_secure = os.getenv("ENVIRONMENT") == "production"

    response.set_cookie(
        key="mb_access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
        max_age=ACCESS_COOKIE_MAX_AGE,
    )
    response.set_cookie(
        key="mb_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_COOKIE_MAX_AGE,
    )

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
    response.delete_cookie(
        key="mb_refresh_token",
        path="/",
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
    )
    return {"message": "Logged out successfully"}

@usuario_router.post("/create", response_model=UsuarioRead)
def create_usuario(
    nombre: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    foto_perfil: UploadFile | None = File(None),
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

    existing = db.query(Usuario).filter(Usuario.username == username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username ya existe",
        )

    usuario = UsuarioCreate(nombre=nombre, username=username, password=password)

    try:
        return create_usuario_service_with_photo(db, usuario, foto_perfil)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@usuario_router.put("/profile", response_model=UsuarioRead)
def update_profile(
    nombre: str | None = Form(None),
    username: str | None = Form(None),
    foto_perfil: UploadFile | None = File(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    try:
        return update_usuario_profile(
            db,
            current_user,
            nombre=nombre,
            username=username,
            photo_file=foto_perfil,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@usuario_router.post("/change-password")
def change_password(
    datos: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    if datos.new_password != datos.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las nuevas contraseñas no coinciden",
        )

    try:
        change_password_service(
            db,
            current_user,
            datos.current_password,
            datos.new_password,
        )
        return {"message": "Contraseña actualizada exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

@usuario_router.get("/verify", response_model=UsuarioRead)
async def verify_token_router(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para verificar que el JWT es válido y retorna los datos del usuario.
    Usado en frontend para revalidar sesión al montar.
    Requiere Authorization header con Bearer token.
    """
    current_user.foto_url = _to_public_image_url(current_user.foto_url)
    return current_user


