import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel, Session
from app.models import *  # Importar los modelos

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@database:3306/moretti_blanco")
parsed_url = make_url(DATABASE_URL)
DATABASE_NAME = parsed_url.database or os.getenv("DATABASE_NAME", "moretti_blanco")
DATABASE_URL_MASTER = parsed_url.set(database=None).render_as_string(hide_password=False)
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

_engine = None


def _build_engine(url: str, echo: bool = False):
    return create_engine(
        url,
        echo=echo,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def _ensure_schema_compatibility(engine) -> None:
    """Aplica ajustes mínimos de compatibilidad para instancias ya existentes."""
    with engine.connect() as conn:
        foto_url_exists = conn.execute(
            text(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :schema
                  AND TABLE_NAME = 'usuario'
                  AND COLUMN_NAME = 'foto_url'
                LIMIT 1
                """
            ),
            {"schema": DATABASE_NAME},
        ).scalar()

        if not foto_url_exists:
            conn.execute(text("ALTER TABLE `usuario` ADD COLUMN `foto_url` VARCHAR(255) NULL"))
            conn.commit()
            print("✓ Columna 'foto_url' agregada en tabla 'usuario'")

        cargo_exists = conn.execute(
            text(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :schema
                  AND TABLE_NAME = 'datoscontacto'
                  AND COLUMN_NAME = 'cargo'
                LIMIT 1
                """
            ),
            {"schema": DATABASE_NAME},
        ).scalar()

        if not cargo_exists:
            conn.execute(text("ALTER TABLE `datoscontacto` ADD COLUMN `cargo` VARCHAR(255) NULL"))
            conn.commit()
            print("✓ Columna 'cargo' agregada en tabla 'datoscontacto'")

def create_db_and_tables():
    """Crea la BD y las tablas basadas en los modelos"""
    last_error = None
    for attempt in range(10):
        try:
            engine_master = _build_engine(DATABASE_URL_MASTER, echo=False)

            with engine_master.connect() as conn:
                safe_db_name = DATABASE_NAME.replace("`", "")
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{safe_db_name}`"))
                conn.commit()
                print(f"✓ Base de datos '{safe_db_name}' creada/verificada")

            engine_master.dispose()
            break
        except Exception as exc:
            last_error = exc
            if attempt == 9:
                raise
            time.sleep(2)
    
    engine = get_engine()
    
    SQLModel.metadata.create_all(engine)
    _ensure_schema_compatibility(engine)
    print("✓ Tablas creadas/verificadas desde modelos")

def get_engine():
    """Retorna el engine de SQLAlchemy"""
    global _engine
    if _engine is None:
        _engine = _build_engine(DATABASE_URL, echo=SQL_ECHO)
    return _engine

def get_session():
    """Retorna una sesión de BD"""
    with Session(get_engine()) as session:
        yield session