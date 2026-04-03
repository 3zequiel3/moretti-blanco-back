import os
from pathlib import Path


def get_storage_backend() -> str:
    return os.getenv("STORAGE_BACKEND", "local").strip().lower()


def get_uploads_root() -> Path:
    # Docker local usa /app/uploads montado por volumen.
    raw = os.getenv("UPLOADS_DIR", "/app/uploads").strip()
    return Path(raw)


def ensure_storage_runtime_is_valid() -> None:
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    backend = get_storage_backend()

    if env == "production" and backend != "s3":
        raise RuntimeError(
            "ENVIRONMENT=production requiere STORAGE_BACKEND=s3 para evitar escritura local de archivos"
        )


def is_local_storage() -> bool:
    return get_storage_backend() == "local"
