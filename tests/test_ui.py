"""Pruebas de interfaz con pytest-qt (paso 5): panel, listas y formularios."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from PyQt6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import OrderState, Priority
from luciotech.services.customer_service import CustomerData, save_customer
from luciotech.services.equipment_service import EquipmentData, save_equipment
from luciotech.services.order_service import create_service_order
from luciotech.services.state_service import change_order_state
from luciotech.ui.dialogs.customer_dialog import CustomerDialog
from luciotech.ui.dialogs.equipment_dialog import EquipmentDialog
from luciotech.ui.main_window import MainWindow
from luciotech.ui.pages.customers_page import CustomersPage
from luciotech.ui.pages.equipment_page import EquipmentPage
from luciotech.ui.pages.home_page import HomePage


@pytest.fixture
def seeded(session_factory: sessionmaker[Session]) -> sessionmaker[Session]:
    with session_factory() as session:
        ana = save_customer(
            session,
            CustomerData(nombre_completo="Ana Torres", numero_identificacion="1710034065",
                         telefono_principal="0991234567"),
        )
        save_customer(
            session,
            CustomerData(nombre_completo="Luis Mora", telefono_principal="0987654321"),
        )
        laptop = save_equipment(
            session,
            EquipmentData(cliente_id=ana.id, tipo_equipo="Laptop", marca="HP",
                          numero_serie="SN-1", contrasena_equipo="secreto"),
            ["Laptop", "Otro"],
        )
        order = create_service_order(
            session,
            customer=ana,
            equipment=laptop,
            usuario="Ing. Lucio",
            prioridad=Priority.NORMAL,
            fecha_ingreso=datetime.now(),
            costo_diagnostico=Decimal("20"),
        )
        change_order_state(session, order, OrderState.EN_REPARACION, usuario="Ing. Lucio")
        session.commit()
    return session_factory


def test_home_cards_show_live_counts(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = HomePage(seeded)
    qtbot.addWidget(page)
    assert page.value_text("under_repair") == "1"
    assert page.value_text("received_today") == "1"
    assert page.value_text("pending_diagnosis") == "0"


def test_home_refresh_reflects_new_data(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = HomePage(seeded)
    qtbot.addWidget(page)
    with seeded() as session:
        save_customer(session, CustomerData(nombre_completo="Nuevo", telefono_principal="0911111111"))
        session.commit()
    page.refresh()
    assert page.value_text("under_repair") == "1"


def test_customer_search_filters_rows(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = CustomersPage(seeded)
    qtbot.addWidget(page)
    assert page.visible_row_count() == 2
    page.set_search_text("ana")
    assert page.visible_row_count() == 1
    page.set_search_text("0987654321")
    assert page.visible_row_count() == 1
    page.set_search_text("nadie")
    assert page.visible_row_count() == 0


def test_equipment_list_hides_password(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    page = EquipmentPage(seeded)
    qtbot.addWidget(page)
    assert page.visible_row_count() == 1
    for column in range(5):
        cell = page._table.item(0, column)
        assert cell is not None
        assert "secreto" not in cell.text()


def test_customer_dialog_shows_validation_errors(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    dialog = CustomerDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._name.setText("")
    dialog._identification.setText("1710034066")
    dialog._save()
    text = dialog._error_label.text()
    assert "Campo obligatorio" in text
    assert "dígito verificador" in text
    assert dialog.result() == 0


def test_customer_dialog_saves_valid_customer(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    dialog = CustomerDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._name.setText("Marta Vélez")
    dialog._identification.setText("")
    dialog._phone.setText("0977777777")
    dialog._save()
    with seeded() as session:
        names = {c.nombre_completo for c in session.query(_customer_model()).all()}
    assert "Marta Vélez" in names


def test_customer_dialog_asks_before_saving_duplicate(
    qtbot: QtBot, seeded: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    dialog = CustomerDialog(seeded)
    qtbot.addWidget(dialog)
    dialog._name.setText("Otra Ana")
    dialog._identification.setText("1710034065")
    dialog._save()
    with seeded() as session:
        assert session.query(_customer_model()).filter_by(nombre_completo="Otra Ana").count() == 0


def test_equipment_dialog_hides_password_until_toggled(
    qtbot: QtBot, seeded: sessionmaker[Session]
) -> None:
    from PyQt6.QtWidgets import QLineEdit

    with seeded() as session:
        equipment_id = session.query(_equipment_model()).one().id
    dialog = EquipmentDialog(seeded, equipment_id=equipment_id)
    qtbot.addWidget(dialog)
    assert dialog._password.echoMode() == QLineEdit.EchoMode.Password
    assert dialog._password.text() == "secreto"
    dialog._toggle_password.setChecked(True)
    assert dialog._password.echoMode() == QLineEdit.EchoMode.Normal


def test_main_window_has_three_tabs(qtbot: QtBot, seeded: sessionmaker[Session]) -> None:
    window = MainWindow(seeded)
    qtbot.addWidget(window)
    assert window.home_page.value_text("received_today") == "1"
    assert window.customers_page.visible_row_count() == 2
    assert window.equipment_page.visible_row_count() == 1


def _customer_model():
    from luciotech.database.models import Customer

    return Customer


def _equipment_model():
    from luciotech.database.models import Equipment

    return Equipment
