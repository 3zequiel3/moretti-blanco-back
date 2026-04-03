from fastapi import FastAPI
from app.core.database import create_db_and_tables
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from app.core.storage import ensure_storage_runtime_is_valid, is_local_storage, get_uploads_root

# Setear ENVIRONMENT si no está configurada
if "ENVIRONMENT" not in os.environ:
    os.environ["ENVIRONMENT"] = os.getenv("NODE_ENV", "development")


#routers
from app.routers.carrousel_router import carrousel_router
from app.routers.usuario_router import usuario_router
from app.routers.datos_contacto_router import datos_contacto_router
from app.routers.ultimo_trabajo_router import ultimo_trabajo_router

def _get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("PUBLIC_DOMAIN", "http://localhost:5173")
    parsed = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    defaults = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Keep order and remove duplicates.
    return list(dict.fromkeys([*parsed, *defaults]))


ALLOWED_ORIGINS = _get_allowed_origins()
@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_storage_runtime_is_valid()
    create_db_and_tables()
    yield
    print("Lifespan ended")

app = FastAPI(lifespan=lifespan)

if is_local_storage():
    uploads_dir = get_uploads_root()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(carrousel_router)
app.include_router(usuario_router)
app.include_router(datos_contacto_router)
app.include_router(ultimo_trabajo_router)