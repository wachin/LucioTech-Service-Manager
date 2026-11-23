"""Pruebas del idioma de la aplicación (§21).

El inglés es el idioma fuente y el español viaja compilado en `ui/translations`. La suite
completa instala el español desde `conftest.py`, así que aquí se comprueba que los textos
llegan traducidos y que el idioma elegido se guarda en la configuración.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFontComboBox,
    QListWidget,
    QPlainTextEdit,
    QTabWidget,
    QTableWidget,
    QTextEdit,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import PhotoType, UserRole
from luciotech.services.customer_service import CustomerData
from luciotech.services.equipment_service import EquipmentData
from luciotech.services.predefined_text_service import default_predefined_texts
from luciotech.services.reception_service import ReceptionData, register_reception
from luciotech.services.user_service import CurrentUser
from luciotech.ui import documents
from luciotech.ui.dialogs.budget_payments_tab import BudgetLineDialog, PaymentDialog
from luciotech.ui.dialogs.customer_dialog import CustomerDialog
from luciotech.ui.dialogs.document_chooser_dialog import (
    DESCRIPTIONS,
    DocumentChooserDialog,
)
from luciotech.ui.dialogs.equipment_dialog import EquipmentDialog
from luciotech.ui.dialogs.find_replace_dialog import FindReplaceDialog
from luciotech.ui.dialogs.login_dialog import FirstUserDialog, LoginDialog
from luciotech.ui.dialogs.order_detail_dialog import OrderDetailDialog
from luciotech.ui.dialogs.photographs_tab import PhotoEditDialog
from luciotech.ui.dialogs.reception_dialog import ReceptionDialog
from luciotech.ui.dialogs.settings_dialog import SettingsDialog
from luciotech.ui.dialogs.users_dialog import UsersDialog
from luciotech.ui.documents import DocumentKind, document_label
from luciotech.ui.widgets.rich_text_editor import RichTextEditor
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


def _visible_texts(root: QWidget) -> list[str]:
    """Todo el texto que puede leer una persona en un diálogo: títulos, botones, tablas…"""
    texts = [root.windowTitle()]
    for action in root.findChildren(QAction):
        texts.extend((action.text(), action.toolTip()))
    for widget in root.findChildren(QWidget):
        for attribute in ("text", "title", "placeholderText"):
            getter = getattr(widget, attribute, None)
            if callable(getter):
                texts.append(getter())
        if isinstance(widget, QComboBox) and not isinstance(widget, QFontComboBox):
            # El selector de fuente lista nombres del sistema, no textos del programa.
            texts.extend(widget.itemText(index) for index in range(widget.count()))
        if isinstance(widget, QTabWidget):
            texts.extend(
                widget.tabText(index) for index in range(widget.count())
            )
        if isinstance(widget, QTableWidget):
            header = widget.horizontalHeader()
            texts.extend(
                header.model().headerData(column, header.orientation())
                for column in range(widget.columnCount())
            )
        if isinstance(widget, QListWidget):
            texts.extend(widget.item(index).text() for index in range(widget.count()))
        if isinstance(widget, (QPlainTextEdit, QTextEdit)):
            texts.append(widget.toPlainText())
    return [text for text in texts if isinstance(text, str) and text.strip()]


def _spanish_phrases() -> list[str]:
    """Traducciones del catálogo que se diferencian del texto inglés fuente."""
    tree = ET.parse(Path(__file__).parents[1] / "translations" / "luciotech_es.ts")
    phrases: set[str] = set()
    for message in tree.iter("message"):
        source = message.findtext("source") or ""
        translation = message.findtext("translation") or ""
        if translation.strip() and translation != source and len(translation.strip()) >= 3:
            phrases.add(translation.strip())
    return sorted(phrases, key=len, reverse=True)


def _spanish_remains(texts: list[str]) -> list[tuple[str, str]]:
    """Parejas (texto mostrado, frase española encontrada) que delatan una traducción."""
    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(phrase) for phrase in _spanish_phrases()) + r")(?!\w)"
    )
    found: list[tuple[str, str]] = []
    for text in texts:
        # Los marcadores ({meses}, {dias}, {orden}) se comparten entre idiomas.
        for match in pattern.finditer(re.sub(r"\{[^}]*\}", " ", text)):
            found.append((text, match.group(1)))
            break
    return found


def _english_order(session_factory: sessionmaker[Session]) -> int:
    """Una orden con datos en inglés para imprimir los documentos sin ruido español."""
    with session_factory() as session:
        order = register_reception(
            session,
            ReceptionData(
                equipment=EquipmentData(
                    cliente_id=None,
                    tipo_equipo="Laptop",
                    marca="Dell",
                    modelo="Inspiron",
                    numero_serie="SN-1",
                    estado_fisico="Minor scratch",
                    accesorios_recibidos="charger",
                ),
                new_customer=CustomerData(
                    nombre_completo="Jane Roe",
                    numero_identificacion="1301206320",
                    telefono_principal="0991234567",
                ),
                fecha_ingreso=datetime(2026, 3, 10, 9, 0),
                tecnico_responsable="Jane Roe",
                costo_diagnostico=Decimal("100"),
                anticipo=Decimal("20"),
            ),
        )
        session.commit()
        return order.id


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

        order_id = _english_order(session_factory)
        admin = CurrentUser(1, "admin", "Jane Roe", UserRole.ADMINISTRADOR.value)
        dialogs: list[QDialog] = [
            LoginDialog(session_factory),
            FirstUserDialog(session_factory),
            CustomerDialog(session_factory),
            EquipmentDialog(session_factory),
            ReceptionDialog(session_factory, "Jane Roe"),
            SettingsDialog(session_factory),
            DocumentChooserDialog(),
            BudgetLineDialog(),
            PaymentDialog(),
            PhotoEditDialog("", PhotoType.EQUIPO_REPARADO.value),
            FindReplaceDialog(RichTextEditor()),
            OrderDetailDialog(session_factory, order_id, "Jane Roe"),
            UsersDialog(session_factory, admin),
        ]
        for dialog in dialogs:
            qtbot.addWidget(dialog)
            leftovers = _spanish_remains(_visible_texts(dialog))
            assert not leftovers, f"{type(dialog).__name__}: {leftovers[:1]}"

        with session_factory() as session:
            order = session.get(documents.ServiceOrder, order_id)
            assert order is not None
            htmls = {
                "receipt": documents.receipt_html(session, order),
                "budget": documents.budget_html(session, order),
                "technical": documents.technical_report_html(session, order),
                "delivery": documents.delivery_html(session, order),
                "history": documents.history_html(session, order),
            }
        for name, html in htmls.items():
            visible = re.sub(r"<[^>]+>", " ", html)
            leftovers = _spanish_remains([visible])
            assert not leftovers, f"{name}: {leftovers[:1]}"
        doc_texts = [document_label(kind) for kind in DocumentKind]
        doc_texts += [dialog.tr(DESCRIPTIONS[kind.value]) for kind in DocumentKind]
        assert not _spanish_remains(doc_texts)
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
