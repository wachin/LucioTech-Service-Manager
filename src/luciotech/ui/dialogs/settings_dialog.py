"""Pantalla de Configuración (§5.8): taller, documentos y textos legales.

Aquí se editan **todos** los términos y condiciones y la garantía. Se guardan en la tabla
`configuracion` y los documentos de §13.1 los leen al imprimir, así que un cambio alcanza a
todos los papeles sin tocar el código ni reimprimir con una plantilla vieja.
"""

from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import (
    DEFAULT_LANGUAGE,
    MAX_PAGE_MARGIN_MM,
    MIN_PAGE_MARGIN_MM,
    PAPER_SIZES,
)
from luciotech.services.settings_service import (
    budget_validity_days,
    default_service_terms,
    default_warranty_terms,
    language,
    equipment_types,
    page_margin_mm,
    paper_size,
    retention_months,
    service_terms,
    set_budget_validity_days,
    set_equipment_types,
    set_language,
    set_page_margin_mm,
    set_paper_size,
    set_retention_months,
    set_service_terms,
    set_tax_settings,
    set_warranty_days,
    set_warranty_terms,
    set_workshop_details,
    tax_settings,
    warranty_days,
    warranty_terms,
    workshop_address,
    workshop_email,
    workshop_name,
    workshop_phone,
)
from luciotech.ui.labels import equipment_type_label, equipment_type_value
from luciotech.ui.translations import available_languages

ERROR_STYLE = "color: #b00020;"
TAB_TALLER = "Workshop"
TAB_DOCUMENTOS = "Documents"
TAB_LEGAL = "Terms and warranty"


class SettingsDialog(QDialog):
    """Edita la configuración de negocio; solo escribe al pulsar Guardar."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._language_changed = False
        self._saved_language = DEFAULT_LANGUAGE
        self.setWindowTitle(self.tr("Settings"))
        self.setMinimumSize(720, 580)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._workshop_tab(), self.tr(TAB_TALLER))
        self._tabs.addTab(self._documents_tab(), self.tr(TAB_DOCUMENTOS))
        self._tabs.addTab(self._legal_tab(), self.tr(TAB_LEGAL))

        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setStyleSheet(ERROR_STYLE)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._save)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._tabs)
        layout.addWidget(self._message)
        layout.addWidget(self._buttons)

        self._load()

    def _workshop_tab(self) -> QWidget:
        self._name = QLineEdit()
        self._phone = QLineEdit()
        self._email = QLineEdit()
        self._address = QLineEdit()
        self._tax_percent = QDoubleSpinBox()
        self._tax_percent.setRange(0, 100)
        self._tax_percent.setDecimals(2)
        self._tax_percent.setSuffix(" %")
        self._tax_enabled = QCheckBox(self.tr("Tax enabled"))
        self._language = QComboBox()
        for code, name in available_languages().items():
            self._language.addItem(name, code)

        form = QFormLayout()
        form.addRow(self.tr("Workshop name"), self._name)
        form.addRow(self.tr("Phone"), self._phone)
        form.addRow(self.tr("Email"), self._email)
        form.addRow(self.tr("Address"), self._address)
        form.addRow(self.tr("Tax percentage"), self._tax_percent)
        form.addRow("", self._tax_enabled)
        form.addRow(self.tr("Language"), self._language)

        note = QLabel(
            self.tr(
                "These details appear in the header of every document. Workshop prices "
                "already include tax, so tax starts disabled."
            )
        )
        note.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch(1)
        return _tab(layout)

    def _documents_tab(self) -> QWidget:
        self._paper = QComboBox()
        for name in PAPER_SIZES:
            self._paper.addItem(name, name)
        self._margin = QSpinBox()
        self._margin.setRange(MIN_PAGE_MARGIN_MM, MAX_PAGE_MARGIN_MM)
        self._margin.setSuffix(" mm")
        self._budget_days = QSpinBox()
        self._budget_days.setRange(1, 365)
        self._budget_days.setSuffix(self.tr(" days"))
        self._retention = QSpinBox()
        self._retention.setRange(1, 120)
        self._retention.setSuffix(self.tr(" months"))
        self._equipment_types = QPlainTextEdit()
        self._equipment_types.setMaximumHeight(110)

        form = QFormLayout()
        form.addRow(self.tr("Paper size"), self._paper)
        form.addRow(self.tr("Page margins"), self._margin)
        form.addRow(self.tr("Budget validity"), self._budget_days)
        form.addRow(self.tr("Deadline to collect equipment"), self._retention)
        form.addRow(self.tr("Equipment types (one per line)"), self._equipment_types)

        note = QLabel(
            self.tr(
                "The collection deadline replaces the {meses} placeholder in the terms and "
                "conditions. If the type list is left empty, the default values return."
            )
        )
        note.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch(1)
        return _tab(layout)

    def _legal_tab(self) -> QWidget:
        self._warranty_days = QSpinBox()
        self._warranty_days.setRange(0, 3650)
        self._warranty_days.setSuffix(self.tr(" days"))

        self._service_terms = QPlainTextEdit()
        self._service_terms.setMinimumHeight(150)
        self._warranty_terms = QPlainTextEdit()
        self._warranty_terms.setMinimumHeight(150)

        self._reset_terms = QPushButton(self.tr("Restore default text"))
        self._reset_terms.clicked.connect(self._restore_service_terms)
        self._reset_warranty = QPushButton(self.tr("Restore default text"))
        self._reset_warranty.clicked.connect(self._restore_warranty_terms)

        days_form = QFormLayout()
        days_form.addRow(
            self.tr("Warranty days (new orders and orders without their own warranty)"),
            self._warranty_days,
        )

        terms_hint = QLabel(
            self.tr(
                "Terms and conditions: printed on the four documents handed to the customer. "
                "The {meses} placeholder is replaced by the deadline from Documents."
            )
        )
        warranty_hint = QLabel(
            self.tr(
                "Warranty conditions: same documents, placeholders {dias}, {orden} and "
                "{meses}. Leaving the text empty removes the section."
            )
        )
        note = QLabel(
            self.tr(
                "An order with its own days keeps its warranty; one without uses the value "
                "here. Setting 0 days removes the warranty from every document."
            )
        )
        for label in (terms_hint, warranty_hint, note):
            label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addLayout(days_form)
        layout.addWidget(terms_hint)
        layout.addLayout(_with_button(self._service_terms, self._reset_terms))
        layout.addWidget(warranty_hint)
        layout.addLayout(_with_button(self._warranty_terms, self._reset_warranty))
        layout.addWidget(note)
        return _tab(layout)

    def _load(self) -> None:
        """Trae a la pantalla lo que hay guardado; lo que falta sale de `config.py`."""
        try:
            with self._session_factory() as session:
                tax = tax_settings(session)
                self._name.setText(workshop_name(session))
                self._phone.setText(workshop_phone(session))
                self._email.setText(workshop_email(session))
                self._address.setText(workshop_address(session))
                self._tax_percent.setValue(float(tax.percent))
                self._tax_enabled.setChecked(tax.enabled)
                index = self._paper.findData(paper_size(session))
                self._paper.setCurrentIndex(max(index, 0))
                self._margin.setValue(page_margin_mm(session))
                self._budget_days.setValue(budget_validity_days(session))
                self._retention.setValue(retention_months(session))
                self._equipment_types.setPlainText(
                    "\n".join(equipment_type_label(tipo) for tipo in equipment_types(session))
                )
                self._warranty_days.setValue(warranty_days(session))
                self._service_terms.setPlainText(service_terms(session))
                self._warranty_terms.setPlainText(warranty_terms(session))
                self._saved_language = language(session)
                index = self._language.findData(self._saved_language)
                if index >= 0:
                    self._language.setCurrentIndex(index)
        except (ValueError, SQLAlchemyError) as exc:
            self._message.setText(
                self.tr("The settings could not be read: %1").replace("%1", str(exc))
            )

    def _save(self) -> None:
        try:
            with self._session_factory() as session:
                set_workshop_details(
                    session,
                    name=self._name.text(),
                    phone=self._phone.text(),
                    email=self._email.text(),
                    address=self._address.text(),
                )
                set_tax_settings(
                    session,
                    Decimal(str(self._tax_percent.value())),
                    self._tax_enabled.isChecked(),
                )
                set_paper_size(session, self._paper.currentData())
                set_page_margin_mm(session, self._margin.value())
                set_budget_validity_days(session, self._budget_days.value())
                set_retention_months(session, self._retention.value())
                set_equipment_types(
                    session,
                    "\n".join(
                        equipment_type_value(line)
                        for line in self._equipment_types.toPlainText().splitlines()
                    ),
                )
                set_warranty_days(session, self._warranty_days.value())
                set_service_terms(session, self._service_terms.toPlainText())
                set_warranty_terms(session, self._warranty_terms.toPlainText())
                set_language(session, self._language.currentData())
                session.commit()
        except (ValueError, SQLAlchemyError) as exc:
            self._message.setText(
                self.tr("The settings could not be saved: %1").replace("%1", str(exc))
            )
            return
        self._language_changed = self._language.currentData() != self._saved_language
        if self._language_changed:
            QMessageBox.information(
                self,
                self.windowTitle(),
                self.tr("The language takes effect the next time the application starts."),
            )
        self.accept()

    def _restore_service_terms(self) -> None:
        self._service_terms.setPlainText(default_service_terms())

    def _restore_warranty_terms(self) -> None:
        self._warranty_terms.setPlainText(default_warranty_terms())


def _tab(layout: QVBoxLayout) -> QWidget:
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def _with_button(editor: QPlainTextEdit, button: QPushButton) -> QHBoxLayout:
    """El editor de texto legal con su botón de restablecer a la derecha."""
    row = QHBoxLayout()
    row.addWidget(editor, 1)
    row.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
    return row
