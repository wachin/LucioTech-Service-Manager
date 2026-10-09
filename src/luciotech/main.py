"""Punto de entrada de LucioTech Service Manager."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from luciotech.config import APP_CONFIG, APP_VERSION
from luciotech.database.connection import (
    create_db_engine,
    create_session_factory,
    resolve_database_url,
)
from luciotech.database.migrate import upgrade_database
from luciotech.ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName(APP_CONFIG.app_name)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_CONFIG.organization_name)

    url = resolve_database_url()
    upgrade_database(url)
    engine = create_db_engine(url)
    window = MainWindow(create_session_factory(engine))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
