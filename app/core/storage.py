import os
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from botocore.client import BaseClient
from botocore.config import Config


def get_storage_backend() -> str:
    return os.getenv("STORAGE_BACKEND", "local").strip().lower()


def is_s3_storage() -> bool:
    return get_storage_backend() == "s3"


def get_uploads_root() -> Path:
    # Docker local usa /app/uploads montado por volumen.
    raw = os.getenv("UPLOADS_DIR", "/app/uploads").strip()
    return Path(raw)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default

    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta variable requerida para S3: {name}")
    return value


def get_s3_key_prefix() -> str:
    return os.getenv("S3_UPLOAD_PREFIX", "uploads").strip().strip("/")


def get_s3_public_base_url() -> str:
    explicit_base = os.getenv("S3_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if explicit_base:
        return explicit_base

    endpoint = _get_required_env("S3_ENDPOINT").strip().rstrip("/")
    bucket = _get_required_env("S3_BUCKET_NAME").strip()
    return f"{endpoint}/{bucket}"


def get_public_url_for_storage_path(relative_storage_path: str) -> str:
    sanitized_relative = relative_storage_path.lstrip("/")

    if is_local_storage():
        return f"/uploads/{sanitized_relative}"

    key_prefix = get_s3_key_prefix()
    object_key = f"{key_prefix}/{sanitized_relative}" if key_prefix else sanitized_relative
    return f"{get_s3_public_base_url()}/{object_key}"


def _build_s3_client() -> BaseClient:
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "STORAGE_BACKEND=s3 requiere boto3 instalado. "
            "Agrega boto3 a requirements.txt."
        ) from exc

    endpoint = _get_required_env("S3_ENDPOINT")
    region = _get_required_env("S3_REGION")
    access_key = _get_required_env("S3_ACCESS_KEY")
    secret_key = _get_required_env("S3_SECRET_KEY")

    client_config = Config(
        region_name=region,
        signature_version="s3v4",
        s3={"addressing_style": "path" if _env_flag("S3_FORCE_PATH_STYLE", False) else "auto"},
    )

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=client_config,
    )


def save_uploaded_file(
    *,
    file_obj: BinaryIO,
    original_filename: str | None,
    folder: str,
    allowed_extensions: set[str],
    content_type: str | None = None,
) -> str:
    file_ext = Path(original_filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"Extensión no permitida. Solo se permiten: {allowed}")

    clean_folder = folder.strip().strip("/")
    if not clean_folder:
        raise ValueError("folder no puede ser vacío")

    unique_filename = f"{uuid4()}{file_ext}"
    relative_storage_path = f"{clean_folder}/{unique_filename}"

    if is_local_storage():
        output_file = get_uploads_root() / relative_storage_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        file_obj.seek(0)
        with output_file.open("wb") as buffer:
            buffer.write(file_obj.read())
        return get_public_url_for_storage_path(relative_storage_path)

    bucket = _get_required_env("S3_BUCKET_NAME")
    key_prefix = get_s3_key_prefix()
    object_key = f"{key_prefix}/{relative_storage_path}" if key_prefix else relative_storage_path

    extra_args: dict[str, str] | None = None
    if content_type:
        extra_args = {"ContentType": content_type}

    file_obj.seek(0)
    s3_client = _build_s3_client()
    if extra_args:
        s3_client.upload_fileobj(file_obj, bucket, object_key, ExtraArgs=extra_args)
    else:
        s3_client.upload_fileobj(file_obj, bucket, object_key)

    return get_public_url_for_storage_path(relative_storage_path)


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

        # Valida dependencias/credenciales básicas al inicio para fallar rápido.
        _build_s3_client()


def is_local_storage() -> bool:
    return get_storage_backend() == "local"
