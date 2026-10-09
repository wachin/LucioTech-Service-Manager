"""Conexión a SQLite mediante SQLAlchemy."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from luciotech.utils.paths import database_path

DATABASE_URL_ENV = "LUCIOTECH_DATABASE_URL"


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


def resolve_database_url() -> str:
    """URL de la base: variable de entorno si existe, o la ruta por defecto."""
    return os.environ.get(DATABASE_URL_ENV) or sqlite_url(database_path())


def create_db_engine(url: str | None = None) -> Engine:
    """Crea el motor SQLite, asegurando la carpeta y las claves foráneas."""
    url = url or resolve_database_url()
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
