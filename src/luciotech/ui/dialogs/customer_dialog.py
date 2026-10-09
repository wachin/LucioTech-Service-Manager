"""Formulario de cliente con validación y advertencia de posibles duplicados (§7.1)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.models import Customer
from luciotech.services.customer_service import (
    CustomerData,
    CustomerValidationError,
    customer_input_errors,
    find_possible_duplicates,
    save_customer,
)
from luciotech.ui.validation_texts import error_text, field_label


class CustomerDialog(QDialog):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        customer_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._customer_id = customer_id
        self.setWindowTitle(self.tr("Editar cliente") if customer_id else self.tr("Nuevo cliente"))
        self.setMinimumWidth(480)

        self._name = QLineEdit()
        self._identification = QLineEdit()
        self._phone = QLineEdit()
        self._phone_secondary = QLineEdit()
        self._email = QLineEdit()
        self._address = QPlainTextEdit()
        self._address.setFixedHeight(60)
        self._notes = QPlainTextEdit()
        self._notes.setFixedHeight(60)

        form = QFormLayout()
        form.addRow(field_label("nombre_completo") + " *", self._name)
        form.addRow(field_label("numero_identificacion"), self._identification)
        form.addRow(field_label("telefono_principal"), self._phone)
        form.addRow(field_label("telefono_secundario"), self._phone_secondary)
        form.addRow(field_label("correo_electronico"), self._email)
        form.addRow(self.tr("Dirección"), self._address)
        form.addRow(self.tr("Observaciones"), self._notes)

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

        if customer_id is not None:
            self._load(customer_id)

    def _load(self, customer_id: int) -> None:
        with self._session_factory() as session:
            customer = session.get(Customer, customer_id)
            if customer is None:
                return
            self._name.setText(customer.nombre_completo)
            self._identification.setText(customer.numero_identificacion or "")
            self._phone.setText(customer.telefono_principal or "")
            self._phone_secondary.setText(customer.telefono_secundario or "")
            self._email.setText(customer.correo_electronico or "")
            self._address.setPlainText(customer.direccion or "")
            self._notes.setPlainText(customer.notas or "")

    def _collect(self) -> CustomerData:
        return CustomerData(
            nombre_completo=self._name.text(),
            numero_identificacion=self._identification.text(),
            telefono_principal=self._phone.text(),
            telefono_secundario=self._phone_secondary.text(),
            correo_electronico=self._email.text(),
            direccion=self._address.toPlainText(),
            notas=self._notes.toPlainText(),
        )

    def _save(self) -> None:
        data = self._collect()
        errors = customer_input_errors(data)
        if errors:
            self._show_errors(errors)
            return
        try:
            with self._session_factory() as session:
                duplicates = [
                    customer
                    for customer in find_possible_duplicates(
                        session, data.numero_identificacion, data.telefono_principal
                    )
                    if customer.id != self._customer_id
                ]
                if duplicates and not self._confirm_duplicates(duplicates):
                    return
                save_customer(session, data, self._customer_id)
                session.commit()
        except CustomerValidationError as exc:
            self._show_errors(exc.errors)
            return
        except SQLAlchemyError:
            QMessageBox.critical(
                self,
                self.windowTitle(),
                self.tr("No se pudo guardar el cliente. Revise los datos e intente de nuevo."),
            )
            return
        self.accept()

    def _confirm_duplicates(self, duplicates: list[Customer]) -> bool:
        lines = "\n".join(
            f"• {customer.nombre_completo} "
            f"({customer.numero_identificacion or '-'}, {customer.telefono_principal or '-'})"
            for customer in duplicates
        )
        message = self.tr(
            "Ya existen clientes con la misma identificación o teléfono:\n\n%1\n\n"
            "¿Desea guardar de todos modos?"
        ).replace("%1", lines)
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
