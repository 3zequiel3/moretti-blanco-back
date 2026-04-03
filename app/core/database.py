import os
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Session
from app.models import *  # Importar los modelos

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@database:3306/moretti_blanco")
DATABASE_URL_MASTER = DATABASE_URL.replace("/moretti_blanco", "")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

_engine = None


def _build_engine(url: str, echo: bool = False):
    return create_engine(
        url,
        echo=echo,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

def create_db_and_tables():
    """Crea la BD y las tablas basadas en los modelos"""
    engine_master = _build_engine(DATABASE_URL_MASTER, echo=False)
    
    with engine_master.connect() as conn:
        conn.execute(text("CREATE DATABASE IF NOT EXISTS moretti_blanco"))
        conn.commit()
        print("✓ Base de datos 'moretti_blanco' creada/verificada")
    
    engine_master.dispose()
    
    engine = get_engine()
    
    SQLModel.metadata.create_all(engine)
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