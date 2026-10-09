"""Pruebas de UI del paso 7: detalle de orden con pytest-qt."""

from __future__ import annotations

from decimal import Decimal

import pytest
from PyQt6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import OrderState, PaymentType
from luciotech.database.models import ServiceOrder
from luciotech.services.customer_service import CustomerData
from luciotech.services.equipment_service import EquipmentData
from luciotech.services.reception_service import ReceptionData, register_reception
from luciotech.ui.dialogs.order_detail_dialog import OrderDetailDialog
from luciotech.ui.pages.orders_page import OrdersPage

USER = "Ing. Lucio"


@pytest.fixture
def order_id(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        order = register_reception(
            session,
            ReceptionData(
                equipment=EquipmentData(cliente_id=None, tipo_equipo="Laptop", marca="HP",
                                        problema_reportado_cliente="No enciende"),
                new_customer=CustomerData(nombre_completo="Ana Torres",
                                          telefono_principal="0991234567"),
                costo_diagnostico=Decimal("100"),
                anticipo=Decimal("20"),
            ),
        )
        session.commit()
        return order.id


def _dialog(qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int) -> OrderDetailDialog:
    dialog = OrderDetailDialog(session_factory, order_id, USER)
    qtbot.addWidget(dialog)
    return dialog


def _stored(session_factory: sessionmaker[Session], order_id: int) -> ServiceOrder:
    with session_factory() as session:
        order = session.get(ServiceOrder, order_id)
        assert order is not None
        return order


def test_summary_shows_balance_and_customer(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    html = dialog._summary.text()
    assert "Ana Torres" in html
    assert "115.00 USD" in html
    assert "95.00 USD" in html


def test_change_state_records_history(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._state_combo.setCurrentIndex(dialog._state_combo.findData(OrderState.EN_REPARACION.value))
    dialog._state_comment.setText("Se revisa la placa")
    dialog._change_state()

    stored = _stored(session_factory, order_id)
    assert stored.estado == OrderState.EN_REPARACION
    with session_factory() as session:
        session_order = session.get(ServiceOrder, order_id)
        comments = [change.comentario for change in session_order.state_changes]
    assert "Se revisa la placa" in comments
    assert dialog._history.rowCount() >= 2


def test_payment_updates_balance(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._payment_type.setCurrentIndex(dialog._payment_type.findData(PaymentType.ABONO.value))
    dialog._payment_amount.setText("30,50")
    dialog._register_payment()

    stored = _stored(session_factory, order_id)
    assert stored.saldo_pendiente == Decimal("64.50")
    assert "Guardado" in dialog._message.text()


def test_invalid_payment_amount_is_reported(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._payment_amount.setText("abc")
    dialog._register_payment()
    assert "Importe no válido" in dialog._message.text()
    assert _stored(session_factory, order_id).saldo_pendiente == Decimal("95.00")


def test_refund_above_paid_is_rejected(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._payment_type.setCurrentIndex(dialog._payment_type.findData(PaymentType.REEMBOLSO.value))
    dialog._payment_amount.setText("10")
    dialog._register_payment()
    assert dialog._message.text() == "No se puede reembolsar más de lo pagado."
    assert _stored(session_factory, order_id).saldo_pendiente == Decimal("95.00")


def test_note_is_added_to_history(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._note_title.setText("Cliente llamó")
    dialog._note_body.setText("Pide llamada por la tarde")
    dialog._add_note()
    titles = [dialog._history.item(row, 1).text() for row in range(dialog._history.rowCount())]
    assert "Cliente llamó" in titles


def test_empty_note_title_is_rejected(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int
) -> None:
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._note_title.setText("   ")
    dialog._add_note()
    assert "título" in dialog._message.text().lower()


def test_delivery_requires_confirmation(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._deliver()
    assert _stored(session_factory, order_id).estado == OrderState.RECIBIDO


def test_delivery_when_confirmed(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    dialog = _dialog(qtbot, session_factory, order_id)
    dialog._deliver()
    stored = _stored(session_factory, order_id)
    assert stored.estado == OrderState.ENTREGADO
    assert stored.fecha_entrega is not None


def test_orders_page_opens_detail_for_selected_row(
    qtbot: QtBot, session_factory: sessionmaker[Session], order_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[int] = []

    def fake_exec(self: OrderDetailDialog) -> int:
        opened.append(self._order_id)
        return 0

    monkeypatch.setattr(OrderDetailDialog, "exec", fake_exec)
    page = OrdersPage(session_factory)
    qtbot.addWidget(page)
    page._table.selectRow(0)
    page.open_selected()
    assert opened == [order_id]
