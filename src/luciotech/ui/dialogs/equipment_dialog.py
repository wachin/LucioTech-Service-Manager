"""Formulario de equipo: cliente, tipo, datos técnicos y contraseña opcional (§7.2)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.models import Equipment, ServiceOrder
from luciotech.database.repositories import CustomerRepository
from luciotech.services.equipment_service import (
    EquipmentData,
    EquipmentValidationError,
    equipment_input_errors,
    find_orders_with_serial,
    save_equipment,
)
from luciotech.services.settings_service import equipment_types
from luciotech.ui.validation_texts import error_text, field_label


class EquipmentDialog(QDialog):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        equipment_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._equipment_id = equipment_id
        self.setWindowTitle(self.tr("Editar equipo") if equipment_id else self.tr("Nuevo equipo"))
        self.setMinimumWidth(520)

        self._customer = QComboBox()
        self._type = QComboBox()
        self._brand = QLineEdit()
        self._model = QLineEdit()
        self._serial = QLineEdit()
        self._color = QLineEdit()
        self._os = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText(self.tr("Opcional"))
        self._toggle_password = QToolButton()
        self._toggle_password.setCheckable(True)
        self._toggle_password.setText(self.tr("Mostrar"))
        self._toggle_password.toggled.connect(self._on_toggle_password)
        self._accessories = QPlainTextEdit()
        self._accessories.setFixedHeight(50)
        self._physical_state = QPlainTextEdit()
        self._physical_state.setFixedHeight(50)
        self._reported_problem = QPlainTextEdit()
        self._reported_problem.setFixedHeight(50)
        self._intake_notes = QPlainTextEdit()
        self._intake_notes.setFixedHeight(50)

        password_row = QHBoxLayout()
        password_row.addWidget(self._password, 1)
        password_row.addWidget(self._toggle_password)

        form = QFormLayout()
        form.addRow(field_label("cliente_id") + " *", self._customer)
        form.addRow(field_label("tipo_equipo") + " *", self._type)
        form.addRow(self.tr("Marca"), self._brand)
        form.addRow(self.tr("Modelo"), self._model)
        form.addRow(self.tr("Número de serie"), self._serial)
        form.addRow(self.tr("Color"), self._color)
        form.addRow(self.tr("Sistema operativo"), self._os)
        form.addRow(self.tr("Contraseña o PIN"), password_row)
        form.addRow(self.tr("Accesorios recibidos"), self._accessories)
        form.addRow(self.tr("Estado físico"), self._physical_state)
        form.addRow(self.tr("Problema reportado"), self._reported_problem)
        form.addRow(self.tr("Observaciones de ingreso"), self._intake_notes)

        self._error_label = QLabel()
        self._error_label.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._error_label)
        layout.addWidget(buttons)

        self._load_choices()
        if equipment_id is not None:
            self._load(equipment_id)

    def _load_choices(self) -> None:
        with self._session_factory() as session:
            for customer in CustomerRepository(session).list_all():
                self._customer.addItem(customer.nombre_completo, customer.id)
            self._type.addItems(equipment_types(session))

    def _load(self, equipment_id: int) -> None:
        with self._session_factory() as session:
            equipment = session.get(Equipment, equipment_id)
            if equipment is None:
                return
            self._select_customer(equipment.cliente_id)
            self._select_or_add_type(equipment.tipo_equipo)
            self._brand.setText(equipment.marca or "")
            self._model.setText(equipment.modelo or "")
            self._serial.setText(equipment.numero_serie or "")
            self._color.setText(equipment.color or "")
            self._os.setText(equipment.sistema_operativo or "")
            self._password.setText(equipment.contrasena_equipo or "")
            self._accessories.setPlainText(equipment.accesorios_recibidos or "")
            self._physical_state.setPlainText(equipment.estado_fisico or "")
            self._reported_problem.setPlainText(equipment.problema_reportado_cliente or "")
            self._intake_notes.setPlainText(equipment.observaciones_ingreso or "")

    def _select_customer(self, customer_id: int) -> None:
        index = self._customer.findData(customer_id)
        if index >= 0:
            self._customer.setCurrentIndex(index)

    def _select_or_add_type(self, tipo: str) -> None:
        index = self._type.findText(tipo)
        if index < 0:
            self._type.addItem(tipo)
            index = self._type.count() - 1
        self._type.setCurrentIndex(index)

    def _on_toggle_password(self, shown: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if shown else QLineEdit.EchoMode.Password
        self._password.setEchoMode(mode)
        self._toggle_password.setText(self.tr("Ocultar") if shown else self.tr("Mostrar"))

    def _collect(self) -> EquipmentData:
        customer_id = self._customer.currentData()
        return EquipmentData(
            cliente_id=int(customer_id) if customer_id is not None else None,
            tipo_equipo=self._type.currentText(),
            marca=self._brand.text(),
            modelo=self._model.text(),
            numero_serie=self._serial.text(),
            color=self._color.text(),
            sistema_operativo=self._os.text(),
            contrasena_equipo=self._password.text(),
            accesorios_recibidos=self._accessories.toPlainText(),
            estado_fisico=self._physical_state.toPlainText(),
            problema_reportado_cliente=self._reported_problem.toPlainText(),
            observaciones_ingreso=self._intake_notes.toPlainText(),
        )

    def _save(self) -> None:
        data = self._collect()
        try:
            with self._session_factory() as session:
                allowed = equipment_types(session)
                errors = equipment_input_errors(data, allowed)
                if errors:
                    self._show_errors(errors)
                    return
                conflicts = [
                    order
                    for order in find_orders_with_serial(session, data.numero_serie)
                    if order.equipo_id != self._equipment_id
                ]
                if conflicts and not self._confirm_serial(conflicts):
                    return
                save_equipment(session, data, allowed, self._equipment_id)
                session.commit()
        except EquipmentValidationError as exc:
            self._show_errors(exc.errors)
            return
        except SQLAlchemyError:
            QMessageBox.critical(
                self,
                self.windowTitle(),
                self.tr("No se pudo guardar el equipo. Revise los datos e intente de nuevo."),
            )
            return
        self.accept()

    def _confirm_serial(self, conflicts: list[ServiceOrder]) -> bool:
        numbers = ", ".join(order.numero_orden for order in conflicts)
        message = self.tr(
            "El número de serie ya aparece en las órdenes: %1.\n\n¿Desea guardar de todos modos?"
        ).replace("%1", numbers)
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
