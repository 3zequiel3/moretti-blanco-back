import os
from pathlib import Path


def get_storage_backend() -> str:
    return os.getenv("STORAGE_BACKEND", "local").strip().lower()


def is_s3_storage() -> bool:
    return get_storage_backend() == "s3"


def get_uploads_root() -> Path:
    # Docker local usa /app/uploads montado por volumen.
    raw = os.getenv("UPLOADS_DIR", "/app/uploads").strip()
    return Path(raw)


def ensure_storage_runtime_is_valid() -> None:
    backend = get_storage_backend()
    allowed_backends = {"local", "s3"}

    if backend not in allowed_backends:
        raise RuntimeError(
            "STORAGE_BACKEND invalido. Valores permitidos: local, s3"
        )

    if backend == "s3":
        required_vars = [
            "S3_ENDPOINT",
            "S3_BUCKET_NAME",
            "S3_REGION",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
        ]
        missing_vars = [name for name in required_vars if not os.getenv(name)]
        if missing_vars:
            missing = ", ".join(missing_vars)
            raise RuntimeError(
                f"STORAGE_BACKEND=s3 requiere variables faltantes: {missing}"
            )


def is_local_storage() -> bool:
    return get_storage_backend() == "local"
