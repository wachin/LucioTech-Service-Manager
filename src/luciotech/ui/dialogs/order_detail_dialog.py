"""Detalle de una orden: resumen, cambio de estado, pagos, notas, entrega e historial (§9)."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import OrderState, PaymentMethod, PaymentType
from luciotech.database.models import ServiceOrder
from luciotech.services.order_detail_service import (
    PaymentValidationError,
    add_note,
    mark_delivered,
    order_timeline,
    register_payment,
)
from luciotech.services.state_service import change_order_state
from luciotech.ui.formatting import format_datetime, format_money
from luciotech.ui.validation_texts import error_text

HISTORY_COLUMNS = ("Fecha", "Tipo", "Detalle", "Usuario")


class OrderDetailDialog(QDialog):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        order_id: int,
        usuario: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._order_id = order_id
        self._usuario = usuario
        self.setWindowTitle(self.tr("Orden de servicio"))
        self.setMinimumSize(760, 560)

        self._summary = QLabel()
        self._summary.setWordWrap(True)
        self._state_combo = QComboBox()
        for state in OrderState:
            self._state_combo.addItem(state.value, state.value)
        self._state_comment = QLineEdit()
        self._state_comment.setPlaceholderText(self.tr("Comentario del cambio (opcional)"))
        change_button = QPushButton(self.tr("Cambiar estado"))
        change_button.clicked.connect(self._change_state)

        self._payment_type = QComboBox()
        for kind in PaymentType:
            self._payment_type.addItem(kind.value, kind.value)
        self._payment_method = QComboBox()
        for method in PaymentMethod:
            self._payment_method.addItem(method.value, method.value)
        self._payment_amount = QLineEdit()
        self._payment_amount.setPlaceholderText("0.00")
        self._payment_reference = QLineEdit()
        self._payment_reference.setPlaceholderText(self.tr("Referencia (opcional)"))
        pay_button = QPushButton(self.tr("Registrar pago"))
        pay_button.clicked.connect(self._register_payment)

        self._note_title = QLineEdit()
        self._note_title.setPlaceholderText(self.tr("Título de la nota"))
        self._note_body = QLineEdit()
        self._note_body.setPlaceholderText(self.tr("Detalle (opcional)"))
        note_button = QPushButton(self.tr("Añadir nota"))
        note_button.clicked.connect(self._add_note)

        deliver_button = QPushButton(self.tr("Marcar como entregado"))
        deliver_button.clicked.connect(self._deliver)

        self._history = QTableWidget(0, len(HISTORY_COLUMNS))
        self._history.setHorizontalHeaderLabels([self.tr(c) for c in HISTORY_COLUMNS])
        self._history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history.verticalHeader().setVisible(False)
        self._history.horizontalHeader().setStretchLastSection(True)

        self._message = QLabel()
        self._message.setWordWrap(True)

        state_row = QHBoxLayout()
        state_row.addWidget(self._state_combo)
        state_row.addWidget(self._state_comment, 1)
        state_row.addWidget(change_button)

        payment_form = QFormLayout()
        payment_row = QHBoxLayout()
        payment_row.addWidget(self._payment_type)
        payment_row.addWidget(self._payment_method)
        payment_row.addWidget(self._payment_amount)
        payment_row.addWidget(self._payment_reference, 1)
        payment_row.addWidget(pay_button)
        payment_form.addRow(self.tr("Pago o reembolso"), payment_row)

        note_row = QHBoxLayout()
        note_row.addWidget(self._note_title, 1)
        note_row.addWidget(self._note_body, 2)
        note_row.addWidget(note_button)

        actions = QGroupBox(self.tr("Acciones"))
        actions_layout = QVBoxLayout(actions)
        actions_layout.addLayout(state_row)
        actions_layout.addLayout(payment_form)
        actions_layout.addLayout(note_row)
        actions_layout.addWidget(deliver_button)

        tabs = QTabWidget()
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        summary_layout.addWidget(self._summary)
        tabs.addTab(summary_tab, self.tr("Resumen"))
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(self._history)
        tabs.addTab(history_tab, self.tr("Historial"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(actions)
        layout.addWidget(self._message)
        layout.addWidget(buttons)

        self.refresh()

    def refresh(self) -> None:
        with self._session_factory() as session:
            order = session.get(ServiceOrder, self._order_id)
            if order is None:
                self._message.setText(self.tr("La orden ya no existe."))
                return
            self.setWindowTitle(f"{self.tr('Orden')} {order.numero_orden}")
            self._summary.setText(_summary_html(order))
            index = self._state_combo.findData(order.estado)
            if index >= 0:
                self._state_combo.setCurrentIndex(index)
            self._fill_history(order)

    def _fill_history(self, order: ServiceOrder) -> None:
        entries = order_timeline(order)
        self._history.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            cells = [format_datetime(entry.fecha), entry.titulo, entry.detalle, entry.usuario]
            for column, value in enumerate(cells):
                self._history.setItem(row, column, QTableWidgetItem(value))

    def _run(self, action: Callable[[Session, ServiceOrder], object]) -> bool:
        """Ejecuta una acción dentro de una sesión, la confirma y refresca la vista."""
        try:
            with self._session_factory() as session:
                order = session.get(ServiceOrder, self._order_id)
                if order is None:
                    raise ValueError(self.tr("La orden ya no existe."))
                action(session, order)
                session.commit()
        except PaymentValidationError as exc:
            self._message.setText("\n".join(error_text(code) for code in exc.errors.values()))
            return False
        except ValueError as exc:
            self._message.setText(str(exc))
            return False
        except SQLAlchemyError:
            QMessageBox.critical(
                self, self.windowTitle(), self.tr("No se pudo guardar. Intente de nuevo.")
            )
            return False
        self._message.setText(self.tr("Guardado."))
        self.refresh()
        return True

    def _change_state(self) -> None:
        nuevo = self._state_combo.currentData()
        comment = self._state_comment.text().strip() or None
        self._run(
            lambda session, order: change_order_state(
                session, order, nuevo, usuario=self._usuario, comentario=comment
            )
        )

    def _register_payment(self) -> None:
        try:
            amount = Decimal(self._payment_amount.text().strip().replace(",", "."))
        except InvalidOperation:
            self._message.setText(error_text("amount.invalid"))
            return
        tipo = self._payment_type.currentData()
        metodo = self._payment_method.currentData()
        reference = self._payment_reference.text()
        self._run(
            lambda session, order: register_payment(
                session, order, tipo=tipo, metodo=metodo, monto=amount,
                usuario=self._usuario, referencia=reference,
            )
        )

    def _add_note(self) -> None:
        title = self._note_title.text()
        body = self._note_body.text()
        self._run(
            lambda session, order: add_note(
                session, order, titulo=title, descripcion=body, usuario=self._usuario
            )
        )

    def _deliver(self) -> None:
        answer = QMessageBox.question(
            self,
            self.windowTitle(),
            self.tr("¿Marcar la orden como entregada?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._run(lambda session, order: mark_delivered(session, order, usuario=self._usuario))


def _summary_html(order: ServiceOrder) -> str:
    equipment = order.equipment
    customer = order.customer
    rows = [
        ("Número de orden", order.numero_orden),
        ("Estado", order.estado),
        ("Prioridad", order.prioridad),
        ("Cliente", f"{customer.nombre_completo} ({customer.telefono_principal or '-'})"),
        ("Equipo", f"{equipment.tipo_equipo} {equipment.marca or ''} {equipment.modelo or ''}".strip()),
        ("Número de serie", equipment.numero_serie or "-"),
        ("Fecha de ingreso", format_datetime(order.fecha_ingreso)),
        ("Fecha estimada", format_datetime(order.fecha_estimada_entrega) or "-"),
        ("Problema reportado", order.problema_reportado or "-"),
        ("Total", format_money(order.total)),
        ("Anticipo", format_money(order.anticipo)),
        ("Saldo pendiente", format_money(order.saldo_pendiente)),
    ]
    body = "".join(
        f"<tr><td><b>{_escape(label)}</b></td><td>{_escape(value)}</td></tr>" for label, value in rows
    )
    return f"<table cellspacing='4'>{body}</table>"


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
