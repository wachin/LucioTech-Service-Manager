"""Punto de entrada de LucioTech Service Manager."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from luciotech.config import APP_CONFIG, APP_VERSION
from luciotech.database.connection import (
    create_db_engine,
    create_session_factory,
    resolve_database_url,
)
from luciotech.database.migrate import upgrade_database
from luciotech.services.settings_service import language, tax_settings
from luciotech.services.totals_service import recalculate_stored_totals
from luciotech.ui.dialogs.login_dialog import login_user
from luciotech.ui.main_window import MainWindow
from luciotech.ui.theme import apply_theme, init_theme_state
from luciotech.ui.translations import install_translations

# Icono de la aplicación y de cada ventana que no fije el suyo.
APP_ICON = Path(__file__).resolve().parent / "ui" / "resources" / "icons" / "app-icon.svg"


def main(argv: list[str] | None = None) -> int:
    # En Linux, permitir que el usuario configure el tema (claro/oscuro) y el tema
    # de iconos con Qt6Ct/Kvantum. La variable debe estar definida antes de crear
    # la QApplication para que el plugin de plataforma la lea.
    if sys.platform.startswith("linux") and "QT_QPA_PLATFORMTHEME" not in os.environ:
        os.environ["QT_QPA_PLATFORMTHEME"] = "qt6ct"
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName(APP_CONFIG.app_name)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_CONFIG.organization_name)
    app.setWindowIcon(QIcon(str(APP_ICON)))
    init_theme_state(app)
    from PyQt6.QtCore import QSettings

    saved_theme = QSettings().value("theme", "system")
    apply_theme(str(saved_theme) if saved_theme else "system")

    url = resolve_database_url()
    upgrade_database(url)
    engine = create_db_engine(url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        chosen_language = language(session)
        if recalculate_stored_totals(session, tax_settings(session)):
            session.commit()
    # Los traductores se instalan antes de abrir el acceso para que la primera ventana ya
    # salga en el idioma elegido. Se guardan en `_translators` para que no los recoja el GC.
    _translators = install_translations(app, chosen_language)

    # Cada vuelta es una sesión: al cerrar sesión la ventana se cierra y se pide el acceso
    # otra vez, sin reiniciar el programa.
    while True:
        user = login_user(session_factory)
        if user is None:
            return 0
        window = MainWindow(session_factory, user)
        window.show()
        app.exec()
        if not window.logout_requested:
            return 0
        window.deleteLater()


if __name__ == "__main__":
    raise SystemExit(main())
