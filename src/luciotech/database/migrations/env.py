"""Entorno de ejecución de Alembic."""

from __future__ import annotations

from alembic import context

from luciotech.database.connection import create_db_engine, resolve_database_url
from luciotech.database.models import Base

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    return config.get_main_option("sqlalchemy.url") or resolve_database_url()


def run_migrations_online() -> None:
    engine = create_db_engine(_database_url())
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
