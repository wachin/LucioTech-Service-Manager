"""Pruebas del paso 5: validación y servicios de clientes y equipos."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.models import Customer, Equipment
from luciotech.database.enums import Priority
from luciotech.services.customer_service import (
    CustomerData,
    CustomerValidationError,
    customer_input_errors,
    find_possible_duplicates,
    save_customer,
)
from luciotech.services.equipment_service import (
    EquipmentData,
    EquipmentValidationError,
    equipment_input_errors,
    find_orders_with_serial,
    save_equipment,
)
from luciotech.services.order_service import create_service_order
from luciotech.services.settings_service import KEY_EQUIPMENT_TYPES, equipment_types, set_value
from luciotech.utils.validators import (
    PhoneError,
    email_is_valid,
    phone_error,
)

TYPES = ["Laptop", "Impresora", "Otro"]


def valid_customer(**overrides: str | None) -> CustomerData:
    values: dict[str, str | None] = {
        "nombre_completo": "Juan Pérez",
        "numero_identificacion": "1710034065",
        "telefono_principal": "0991234567",
    }
    values.update(overrides)
    return CustomerData(**values)  # type: ignore[arg-type]


# Validación de teléfono y correo


@pytest.mark.parametrize("value", ["0991234567", "+593 99 123 4567", "(02) 234-5678"])
def test_valid_phones_are_accepted(value: str) -> None:
    assert phone_error(value) is None


def test_phone_with_letters_is_rejected() -> None:
    assert phone_error("099ABC4567") == PhoneError.INVALID_CHARS


@pytest.mark.parametrize("value", ["12345", "1234567890123456"])
def test_phone_length_is_checked(value: str) -> None:
    assert phone_error(value) == PhoneError.LENGTH


@pytest.mark.parametrize(
    ("value", "expected"),
    [("ana@correo.com", True), (" ana@correo.com ", True), ("ana.correo.com", False), ("a@b", False)],
)
def test_email_validation(value: str, expected: bool) -> None:
    assert email_is_valid(value) is expected


# Validación de cliente


def test_valid_customer_has_no_errors() -> None:
    assert customer_input_errors(valid_customer()) == {}


def test_customer_name_is_required() -> None:
    assert customer_input_errors(valid_customer(nombre_completo="  ")) == {
        "nombre_completo": "required"
    }


def test_ten_digit_identification_is_validated_as_cedula() -> None:
    errors = customer_input_errors(valid_customer(numero_identificacion="1710034066"))
    assert errors == {"numero_identificacion": "cedula.check_digit"}


def test_non_cedula_identification_is_not_checked_as_cedula() -> None:
    assert customer_input_errors(valid_customer(numero_identificacion="RUC-123")) == {}


def test_invalid_phone_and_email_are_reported_by_field() -> None:
    errors = customer_input_errors(
        valid_customer(telefono_principal="abc", correo_electronico="sin-arroba")
    )
    assert errors == {"telefono_principal": "phone.invalid_chars", "correo_electronico": "email.invalid"}


def test_save_customer_rejects_invalid_data(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        with pytest.raises(CustomerValidationError) as exc:
            save_customer(session, valid_customer(nombre_completo=""))
        assert exc.value.errors == {"nombre_completo": "required"}
        assert session.query(Customer).count() == 0


def test_save_customer_creates_and_updates(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        customer = save_customer(session, valid_customer(correo_electronico=" ana@correo.com "))
        session.commit()
        customer_id = customer.id

        save_customer(
            session,
            valid_customer(nombre_completo="Juan Pérez Ruiz", correo_electronico="ana@correo.com"),
            customer_id,
        )
        session.commit()

        stored = session.get(Customer, customer_id)
        assert stored is not None
        assert stored.nombre_completo == "Juan Pérez Ruiz"
        assert stored.correo_electronico == "ana@correo.com"


def test_duplicate_customer_is_found_by_identification(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        existing = save_customer(session, valid_customer())
        session.commit()
        assert find_possible_duplicates(session, numero_identificacion="1710034065") == [existing]


def test_duplicate_customer_is_found_by_phone_with_format(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        existing = save_customer(session, valid_customer())
        session.commit()
        assert find_possible_duplicates(session, telefono="099 123-4567") == [existing]


# Equipos


def make_customer(session: Session) -> Customer:
    customer = save_customer(session, valid_customer())
    session.commit()
    return customer


def test_equipment_requires_customer_and_known_type() -> None:
    data = EquipmentData(cliente_id=None, tipo_equipo="Televisor")
    assert equipment_input_errors(data, TYPES) == {
        "cliente_id": "required",
        "tipo_equipo": "invalid_type",
    }


def test_equipment_requires_type() -> None:
    data = EquipmentData(cliente_id=1, tipo_equipo=" ")
    assert equipment_input_errors(data, TYPES) == {"tipo_equipo": "required"}


def test_save_equipment_with_optional_password(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        customer = make_customer(session)
        saved = save_equipment(
            session, EquipmentData(cliente_id=customer.id, tipo_equipo="Laptop", marca=" HP "), TYPES
        )
        session.commit()
        assert saved.marca == "HP"
        assert saved.contrasena_equipo is None

        saved.contrasena_equipo = "1234"
        session.commit()
        assert session.get(Equipment, saved.id).contrasena_equipo == "1234"


def test_save_equipment_rejects_unknown_customer(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        with pytest.raises(EquipmentValidationError) as exc:
            save_equipment(session, EquipmentData(cliente_id=999, tipo_equipo="Laptop"), TYPES)
        assert exc.value.errors == {"cliente_id": "not_found"}


def test_duplicate_serial_warns_with_existing_orders(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        customer = make_customer(session)
        equipment = save_equipment(
            session,
            EquipmentData(cliente_id=customer.id, tipo_equipo="Laptop", numero_serie="SN-1"),
            TYPES,
        )
        order = create_service_order(
            session,
            customer=customer,
            equipment=equipment,
            usuario="Ing. Lucio",
            prioridad=Priority.NORMAL,
            fecha_ingreso=datetime(2026, 3, 10, 9, 0),
            costo_diagnostico=Decimal("10"),
        )
        session.commit()
        assert find_orders_with_serial(session, "sn-1") == [order]


# Tipos de equipo configurables


def test_equipment_types_default_and_custom(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        assert "Laptop" in equipment_types(session)
        set_value(session, KEY_EQUIPMENT_TYPES, "Teclado\n\nRadio\n")
        session.commit()
        assert equipment_types(session) == ["Teclado", "Radio"]
