"""Pruebas de UI del paso 6: formulario de recepción y lista de órdenes con pytest-qt."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import OrderState, Priority
from luciotech.database.models import ServiceOrder
from luciotech.services.customer_service import CustomerData, save_customer
from luciotech.services.equipment_service import EquipmentData, save_equipment
from luciotech.services.order_service import create_service_order
from luciotech.services.reception_service import ReceptionData, register_reception
from luciotech.services.state_service import change_order_state
from luciotech.ui.dialogs.reception_dialog import NEW_CUSTOMER_KEY, ReceptionDialog
from luciotech.ui.main_window import MainWindow
from luciotech.ui.pages.orders_page import OrdersPage

ENTRY = datetime(2026, 3, 10, 9, 0)


@pytest.fixture
def seeded(session_factory: sessionmaker[Session]) -> sessionmaker[Session]:
    with session_factory() as session:
        ana = save_customer(
            session,
            CustomerData(nombre_completo="Ana Torres", numero_identificacion="1710034065",
                         telefono_principal="0991234567"),
        )
        laptop = save_equipment(
            session,
            EquipmentData(cliente_id=ana.id, tipo_equipo="Laptop", marca="HP", modelo="15"),
            ["Laptop", "Impresora"],
        )
        order = create_service_order(
            session,
            customer=ana,
            equipment=laptop,
            usuario="Ing. Lucio",
            prioridad=Priority.ALTA,
            fecha_ingreso=ENTRY,
            costo_diagnostico=Decimal("20"),
        )
        change_order_state(session, order, OrderState.EN_REPARACION, usuario="Ing. Lucio")
        session.commit()
    return session_factory


def _fill_new_customer_reception(dialog: ReceptionDialog, name: str = "Marta Vélez") -> None:
    dialog._customer_combo.setCurrentIndex(dialog._customer_combo.findData(NEW_CUSTOMER_KEY))
    dialog._new_name.setText(name)
    dialog._new_phone.setText("0977777777")
    dialog._type.setCurrentText("Laptop")
    dialog._problem.setPlainText("No enciende")


def test_orders_list_shows_active_orders(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = OrdersPage(seeded)
    qtbot.addWidget(page)
    assert page.visible_row_count() == 1
    assert page.order_number_at(0) == "OT-2026-000001"


def test_orders_text_filter(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = OrdersPage(seeded)
    qtbot.addWidget(page)
    page._text.setText("hp")
    assert page.visible_row_count() == 1
    page._text.setText("nadie")
    assert page.visible_row_count() == 0


def test_orders_state_filter(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = OrdersPage(seeded)
    qtbot.addWidget(page)
    page._state.setCurrentIndex(page._state.findData(OrderState.RECIBIDO.value))
    assert page.visible_row_count() == 0
    page._state.setCurrentIndex(page._state.findData(OrderState.EN_REPARACION.value))
    assert page.visible_row_count() == 1


def test_orders_balance_filter(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = OrdersPage(seeded)
    qtbot.addWidget(page)
    page._only_balance.setChecked(True)
    assert page.visible_row_count() == 1


def test_reception_dialog_shows_next_number(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    assert dialog._number_label.text() == "OT-2026-000002"


def test_new_customer_fields_appear_only_for_new_customer(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._customer_combo.setCurrentIndex(dialog._customer_combo.findData(NEW_CUSTOMER_KEY))
    assert dialog._new_group.isVisibleTo(dialog)
    existing = dialog._customer_combo.findText("Ana Torres")
    dialog._customer_combo.setCurrentIndex(existing)
    assert not dialog._new_group.isVisibleTo(dialog)


def test_reception_saves_new_customer_without_leaving_form(
    qtbot: QtBot, seeded: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    _fill_new_customer_reception(dialog)
    dialog._save()
    assert dialog.saved_order_number == "OT-2026-000002"
    assert dialog.result() == 1


def test_reception_shows_errors_and_saves_nothing(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    _fill_new_customer_reception(dialog, name="")
    dialog._problem.setPlainText("")
    dialog._save()
    text = dialog._error_label.text()
    assert "Campo obligatorio" in text
    assert dialog.saved_order_number is None
    assert dialog.result() == 0


def test_reception_asks_before_saving_similar_customer(
    qtbot: QtBot, seeded: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[str] = []

    def answer_no(*args: object, **kwargs: object) -> QMessageBox.StandardButton:
        asked.append(str(args[2]))
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", answer_no)
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    _fill_new_customer_reception(dialog, name="Otra Ana")
    dialog._new_identification.setText("1710034065")
    dialog._save()
    assert asked and "Ana Torres" in asked[0]
    assert dialog.saved_order_number is None


def test_accessory_detail_is_enabled_only_when_checked(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._type.setCurrentText("Laptop")
    detail = dialog._accessory_details["Batería"]
    assert not detail.isEnabled()
    dialog._accessory_checks["Batería"].setChecked(True)
    assert detail.isEnabled()
    dialog._accessory_checks["Batería"].setChecked(False)
    assert not detail.isEnabled()


def test_accessory_model_is_saved_with_its_item(
    qtbot: QtBot, seeded: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    _fill_new_customer_reception(dialog, name="Pedro Ruiz")
    dialog._accessory_checks["Batería"].setChecked(True)
    dialog._accessory_details["Batería"].setText("Dell XPS 13")
    dialog._accessory_checks["Cargador"].setChecked(True)
    dialog._save()

    with seeded() as session:
        order = session.query(ServiceOrder).order_by(ServiceOrder.id.desc()).first()
        assert order.equipment.accesorios_recibidos == "Cargador, Batería (Dell XPS 13)"


def test_reception_dialog_is_maximized_by_default(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    assert dialog.windowState() & Qt.WindowState.WindowMaximized


def test_main_window_has_orders_tab(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    window = MainWindow(seeded)
    qtbot.addWidget(window)
    assert window.orders_page.visible_row_count() == 1
    assert window._tabs.tabText(1) == "Órdenes"


def _customer_with_equipment(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        customer = save_customer(
            session,
            CustomerData(nombre_completo="Jean Carlos", numero_identificacion="",
                         telefono_principal="0978907244"),
        )
        save_equipment(
            session,
            EquipmentData(cliente_id=customer.id, tipo_equipo="Laptop", marca="Dell",
                          modelo="Inspiron 1750", contrasena_equipo="abc"),
            ["Laptop", "Otro"],
        )
        session.commit()
        return customer.id


def test_equipment_selector_lists_only_the_customers_equipment(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    customer_id = _customer_with_equipment(seeded)
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._customer_combo.setCurrentIndex(dialog._customer_combo.findData(customer_id))
    labels = [dialog._equipment_combo.itemText(i) for i in range(dialog._equipment_combo.count())]
    assert labels == ["— Equipo nuevo —", "Laptop Dell Inspiron 1750"]


def test_choosing_existing_equipment_locks_its_fields(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    customer_id = _customer_with_equipment(seeded)
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._customer_combo.setCurrentIndex(dialog._customer_combo.findData(customer_id))
    dialog._equipment_combo.setCurrentIndex(1)
    assert dialog._brand.text() == "Dell"
    assert not dialog._brand.isEnabled()
    dialog._equipment_combo.setCurrentIndex(0)
    assert dialog._brand.isEnabled()


def test_saving_with_existing_equipment_does_not_create_another(
    qtbot: QtBot, seeded: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    from luciotech.database.models import Equipment

    customer_id = _customer_with_equipment(seeded)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    dialog = ReceptionDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._customer_combo.setCurrentIndex(dialog._customer_combo.findData(customer_id))
    dialog._equipment_combo.setCurrentIndex(1)
    dialog._problem.setPlainText("No carga")
    dialog._save()

    assert dialog.saved_order_number is not None
    with seeded() as session:
        assert session.query(Equipment).filter_by(cliente_id=customer_id).count() == 1


def test_new_order_from_existing_customer_is_registered(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    with seeded() as session:
        register_reception(
            session,
            ReceptionData(
                equipment=EquipmentData(cliente_id=None, tipo_equipo="Laptop"),
                customer_id=1,
                fecha_ingreso=ENTRY,
            ),
        )
        session.commit()
    page = OrdersPage(seeded)
    qtbot.addWidget(page)
    assert page.visible_row_count() == 2
