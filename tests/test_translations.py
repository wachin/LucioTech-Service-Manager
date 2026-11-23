"""Pruebas del idioma de la aplicación (§21).

El inglés es el idioma fuente y el español viaja compilado en `ui/translations`. La suite
completa instala el español desde `conftest.py`, así que aquí se comprueba que los textos
llegan traducidos y que el idioma elegido se guarda en la configuración.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication
from sqlalchemy.orm import Session, sessionmaker

from luciotech.services.settings_service import language, set_language
from luciotech.ui.translations import (
    DEFAULT_LANGUAGE,
    TRANSLATIONS_DIR,
    available_languages,
    install_translations,
)


def test_the_program_texts_speak_spanish(qapp: QApplication) -> None:
    assert QCoreApplication.translate("MainWindow", "Home") == "Inicio"
    assert QCoreApplication.translate("LoginDialog", "Sign in") == "Entrar"
    assert QCoreApplication.translate("LucioTech", "Received") == "Recibido"


def test_qt_dialogs_speak_spanish(qapp: QApplication) -> None:
    assert QCoreApplication.translate("QPrintPreviewDialog", "Print") == "Imprimir"
    assert QCoreApplication.translate("QPrintPreviewDialog", "Page setup") == "Configuración de página"
    assert QCoreApplication.translate("QPlatformTheme", "&Yes") == "&Sí"


def test_the_spanish_catalogue_ships_with_the_package() -> None:
    assert (TRANSLATIONS_DIR / "luciotech_es.qm").is_file()
    assert Path(TRANSLATIONS_DIR).name == "translations"


def test_available_languages_lists_source_and_spanish() -> None:
    languages = available_languages()
    assert languages["en"] == "English"
    assert languages["es"] == "Español"


def test_installing_another_language_returns_the_loaded_files(qapp: QApplication) -> None:
    translators = install_translations(qapp, "es")
    try:
        assert translators
    finally:
        for translator in translators:
            qapp.removeTranslator(translator)


def test_the_language_is_stored_in_the_settings(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        assert language(session) == DEFAULT_LANGUAGE
        set_language(session, "en")
        session.commit()
    with session_factory() as session:
        assert language(session) == "en"
