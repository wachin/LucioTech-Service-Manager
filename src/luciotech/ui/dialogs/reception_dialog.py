"""Formulario de recepción: cliente existente o nuevo, equipo, accesorios y fechas (§7)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import Priority
from luciotech.database.models import Customer
from luciotech.database.repositories import CustomerRepository
from luciotech.services.accessories import build_accessories_text, suggested_accessories
from luciotech.services.customer_service import CustomerData
from luciotech.services.equipment_service import EquipmentData
from luciotech.services.order_number_service import peek_next_order_number
from luciotech.services.reception_service import (
    ReceptionData,
    ReceptionValidationError,
    ReceptionWarnings,
    reception_input_errors,
    reception_warnings,
    register_reception,
)
from luciotech.services.settings_service import equipment_types
from luciotech.ui.validation_texts import error_text, field_label

NEW_CUSTOMER_KEY = -1


class ReceptionDialog(QDialog):
    def __init__(self, session_factory: sessionmaker[Session], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self.saved_order_number: str | None = None
        self.setWindowTitle(self.tr("Nueva recepción"))
        self.setMinimumWidth(640)

        self._customer_combo = QComboBox()
        self._new_name = QLineEdit()
        self._new_identification = QLineEdit()
        self._new_phone = QLineEdit()
        self._new_email = QLineEdit()
        self._new_group = QGroupBox(self.tr("Cliente nuevo"))
        new_form = QFormLayout(self._new_group)
        new_form.addRow(field_label("nombre_completo") + " *", self._new_name)
        new_form.addRow(field_label("numero_identificacion"), self._new_identification)
        new_form.addRow(field_label("telefono_principal"), self._new_phone)
        new_form.addRow(field_label("correo_electronico"), self._new_email)

        self._type = QComboBox()
        self._brand = QLineEdit()
        self._model = QLineEdit()
        self._serial = QLineEdit()
        self._color = QLineEdit()
        self._os = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText(self.tr("Opcional"))
        self._problem = QPlainTextEdit()
        self._problem.setFixedHeight(60)
        self._physical_state = QPlainTextEdit()
        self._physical_state.setFixedHeight(50)
        self._intake_notes = QPlainTextEdit()
        self._intake_notes.setFixedHeight(50)
        self._manual_accessories = QLineEdit()
        self._accessory_checks: list[QCheckBox] = []
        self._accessories_box = QHBoxLayout()
        self._accessories_box.setSpacing(12)

        self._entry = QDateTimeEdit(QDateTime.currentDateTime())
        self._entry.setDisplayFormat("dd/MM/yyyy HH:mm")
        self._estimate = QDateTimeEdit(QDateTime.currentDateTime().addDays(7))
        self._estimate.setDisplayFormat("dd/MM/yyyy HH:mm")
        self._priority = QComboBox()
        self._priority.addItems([p.value for p in Priority])
        self._priority.setCurrentText(Priority.NORMAL.value)
        self._technician = QLineEdit(self.tr("Ing. Lucio"))
        self._diagnosis_cost = QDoubleSpinBox()
        self._diagnosis_cost.setRange(0, 1_000_000)
        self._diagnosis_cost.setDecimals(2)
        self._deposit = QDoubleSpinBox()
        self._deposit.setRange(0, 1_000_000)
        self._deposit.setDecimals(2)

        self._number_label = QLabel()
        self._warning_label = QLabel()
        self._warning_label.setWordWrap(True)
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)

        customer_row = QFormLayout()
        customer_row.addRow(field_label("cliente") + " *", self._customer_combo)

        equipment_form = QFormLayout()
        equipment_form.addRow(field_label("tipo_equipo") + " *", self._type)
        equipment_form.addRow(self.tr("Marca"), self._brand)
        equipment_form.addRow(self.tr("Modelo"), self._model)
        equipment_form.addRow(self.tr("Número de serie"), self._serial)
        equipment_form.addRow(self.tr("Color"), self._color)
        equipment_form.addRow(self.tr("Sistema operativo"), self._os)
        equipment_form.addRow(self.tr("Contraseña o PIN"), self._password)
        equipment_form.addRow(self.tr("Problema reportado *"), self._problem)
        equipment_form.addRow(self.tr("Estado físico"), self._physical_state)
        equipment_form.addRow(self.tr("Observaciones de ingreso"), self._intake_notes)

        accessories_group = QGroupBox(self.tr("Accesorios recibidos"))
        accessories_layout = QVBoxLayout(accessories_group)
        accessories_layout.addLayout(self._accessories_box)
        accessories_layout.addWidget(QLabel(self.tr("Otros accesorios:")))
        accessories_layout.addWidget(self._manual_accessories)

        order_form = QFormLayout()
        order_form.addRow(self.tr("Número de orden"), self._number_label)
        order_form.addRow(self.tr("Fecha y hora de ingreso"), self._entry)
        order_form.addRow(self.tr("Fecha estimada de entrega"), self._estimate)
        order_form.addRow(self.tr("Prioridad"), self._priority)
        order_form.addRow(self.tr("Técnico responsable"), self._technician)
        order_form.addRow(self.tr("Costo inicial de diagnóstico"), self._diagnosis_cost)
        order_form.addRow(self.tr("Anticipo recibido"), self._deposit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(customer_row)
        layout.addWidget(self._new_group)
        layout.addLayout(equipment_form)
        layout.addWidget(accessories_group)
        layout.addLayout(order_form)
        layout.addWidget(self._warning_label)
        layout.addWidget(self._error_label)
        layout.addWidget(buttons)

        self._customer_combo.currentIndexChanged.connect(self._on_customer_changed)
        self._type.currentTextChanged.connect(self._rebuild_accessories)
        self._entry.dateTimeChanged.connect(self._refresh_number)
        self._load_choices()
        self._refresh_number()

    # Carga inicial

    def _load_choices(self) -> None:
        with self._session_factory() as session:
            self._customer_combo.addItem(self.tr("— Cliente nuevo —"), NEW_CUSTOMER_KEY)
            for customer in CustomerRepository(session).list_all():
                self._customer_combo.addItem(customer.nombre_completo, customer.id)
            self._type.addItems(equipment_types(session))
        self._rebuild_accessories(self._type.currentText())
        self._on_customer_changed()

    def _rebuild_accessories(self, tipo: str) -> None:
        for check in self._accessory_checks:
            self._accessories_box.removeWidget(check)
            check.deleteLater()
        self._accessory_checks = []
        for name in suggested_accessories(tipo):
            check = QCheckBox(name)
            self._accessory_checks.append(check)
            self._accessories_box.addWidget(check)
        self._accessories_box.addStretch(1)

    def _on_customer_changed(self) -> None:
        is_new = self._customer_combo.currentData() == NEW_CUSTOMER_KEY
        self._new_group.setVisible(is_new)
        self.adjustSize()

    def _refresh_number(self) -> None:
        year = self._entry.dateTime().toPyDateTime().year
        with self._session_factory() as session:
            self._number_label.setText(peek_next_order_number(session, year))

    # Datos del formulario

    def _collect(self) -> ReceptionData:
        is_new = self._customer_combo.currentData() == NEW_CUSTOMER_KEY
        customer_id = None if is_new else self._customer_combo.currentData()
        new_customer = (
            CustomerData(
                nombre_completo=self._new_name.text(),
                numero_identificacion=self._new_identification.text(),
                telefono_principal=self._new_phone.text(),
                correo_electronico=self._new_email.text(),
            )
            if is_new
            else None
        )
        selected = [check.text() for check in self._accessory_checks if check.isChecked()]
        equipment = EquipmentData(
            cliente_id=None,
            tipo_equipo=self._type.currentText(),
            marca=self._brand.text(),
            modelo=self._model.text(),
            numero_serie=self._serial.text(),
            color=self._color.text(),
            sistema_operativo=self._os.text(),
            contrasena_equipo=self._password.text(),
            accesorios_recibidos=build_accessories_text(selected, self._manual_accessories.text()),
            estado_fisico=self._physical_state.toPlainText(),
            problema_reportado_cliente=self._problem.toPlainText(),
            observaciones_ingreso=self._intake_notes.toPlainText(),
        )
        return ReceptionData(
            equipment=equipment,
            customer_id=int(customer_id) if customer_id is not None else None,
            new_customer=new_customer,
            fecha_ingreso=self._entry.dateTime().toPyDateTime(),
            fecha_estimada_entrega=self._estimate.dateTime().toPyDateTime(),
            prioridad=self._priority.currentText(),
            tecnico_responsable=self._technician.text().strip() or None,
            costo_diagnostico=_decimal(self._diagnosis_cost.value()),
            anticipo=_decimal(self._deposit.value()),
        )

    def _save(self) -> None:
        data = self._collect()
        try:
            with self._session_factory() as session:
                errors = reception_input_errors(session, data)
                if errors:
                    self._show_errors(errors)
                    return
                warnings = reception_warnings(session, data)
                if warnings.has_any and not self._confirm_warnings(warnings):
                    return
                order = register_reception(session, data)
                session.commit()
                self.saved_order_number = order.numero_orden
        except ReceptionValidationError as exc:
            self._show_errors(exc.errors)
            return
        except SQLAlchemyError:
            QMessageBox.critical(
                self,
                self.windowTitle(),
                self.tr("No se pudo registrar la recepción. Intente de nuevo."),
            )
            return
        self.accept()

    def _confirm_warnings(self, warnings: ReceptionWarnings) -> bool:
        lines: list[str] = []
        for customer in warnings.duplicate_customers:
            lines.append(self.tr("Cliente parecido: %1").replace("%1", _customer_label(customer)))
        for order in warnings.serial_orders:
            lines.append(self.tr("Mismo número de serie en la orden %1").replace("%1", order.numero_orden))
        message = "\n".join(lines) + "\n\n" + self.tr("¿Desea registrar la recepción de todos modos?")
        answer = QMessageBox.question(
            self,
            self.windowTitle(),
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _show_errors(self, errors: dict[str, str]) -> None:
        self._error_label.setText(
            "\n".join(f"{field_label(field)}: {error_text(code)}" for field, code in errors.items())
        )


def _decimal(value: float) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def _customer_label(customer: Customer) -> str:
    return f"{customer.nombre_completo} ({customer.telefono_principal or '-'})"
