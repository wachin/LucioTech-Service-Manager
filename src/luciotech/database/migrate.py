"""Aplicación de migraciones de Alembic al arrancar la aplicación."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def upgrade_database(url: str) -> None:
    """Lleva la base indicada a la última revisión, creándola si no existe."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
