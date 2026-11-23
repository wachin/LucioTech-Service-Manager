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

from luciotech.services.predefined_text_service import default_predefined_texts
from luciotech.services.settings_service import (
    default_service_terms,
    default_warranty_terms,
    equipment_types,
    language,
    set_language,
)
from luciotech.ui.labels import (
    equipment_type_label,
    equipment_type_value,
    priority_label,
    state_label,
)
from luciotech.ui.main_window import MainWindow
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


def test_the_interface_speaks_english_without_the_spanish_catalogue(
    qapp: QApplication,
    qtbot,
    session_factory: sessionmaker[Session],
    spanish_translators: list,
) -> None:
    """Sin el catálogo español cargado, la interfaz muestra el inglés fuente."""
    installed = spanish_translators
    for translator in installed:
        qapp.removeTranslator(translator)
    try:
        assert QCoreApplication.translate("LoginDialog", "Sign in") == "Sign in"
        assert state_label("Recibido") == "Received"
        assert priority_label("Alta") == "High"
        assert equipment_type_label("Computadora de escritorio") == "Desktop computer"
        assert equipment_type_value("Desktop computer") == "Computadora de escritorio"

        window = MainWindow(session_factory)
        qtbot.addWidget(window)
        tabs = [window._tabs.tabText(index) for index in range(window._tabs.count())]
        assert tabs == ["Home", "Orders", "Customers", "Equipment", "Trash"]
        assert window.menuBar().actions()[0].text() == "&File"
    finally:
        for translator in installed:
            qapp.installTranslator(translator)


def test_default_texts_follow_the_chosen_language(
    qapp: QApplication,
    session_factory: sessionmaker[Session],
    spanish_translators: list,
) -> None:
    """Los tipos, las frases y los textos legales por defecto hablan el idioma elegido."""
    with session_factory() as session:
        stored_types = equipment_types(session)
    assert "Computadora de escritorio" in stored_types
    assert equipment_type_label("Computadora de escritorio") == "Computadora de escritorio"
    assert default_service_terms().startswith("1. La reparación se inicia")
    assert default_warranty_terms().startswith("1. La garantía cubre")
    assert default_predefined_texts()[0] == "Se realizó inspección visual del equipo."

    installed = spanish_translators
    for translator in installed:
        qapp.removeTranslator(translator)
    try:
        assert equipment_type_label("Computadora de escritorio") == "Desktop computer"
        assert default_service_terms().startswith("1. The repair starts")
        assert default_warranty_terms().startswith("1. The warranty covers")
        assert default_predefined_texts()[0] == (
            "A visual inspection of the equipment was performed."
        )
    finally:
        for translator in installed:
            qapp.installTranslator(translator)


def test_the_language_is_stored_in_the_settings(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        assert language(session) == DEFAULT_LANGUAGE
        set_language(session, "en")
        session.commit()
    with session_factory() as session:
        assert language(session) == "en"
