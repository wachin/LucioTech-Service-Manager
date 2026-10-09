"""Clientes: validación, guardado y detección de duplicados (§7.1 y §18)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from luciotech.database.models import Customer
from luciotech.utils.validators import CEDULA_LENGTH, cedula_error, email_is_valid, phone_error

MIN_PHONE_DIGITS = 7


class CustomerValidationError(ValueError):
    """Lleva un diccionario campo -> código de error para que la UI lo muestre."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Datos de cliente no válidos.")
        self.errors = errors


@dataclass(frozen=True)
class CustomerData:
    nombre_completo: str
    numero_identificacion: str | None = None
    telefono_principal: str | None = None
    telefono_secundario: str | None = None
    correo_electronico: str | None = None
    direccion: str | None = None
    notas: str | None = None


def customer_input_errors(data: CustomerData) -> dict[str, str]:
    """Errores por campo. Una identificación de 10 dígitos se valida como cédula."""
    errors: dict[str, str] = {}
    if not _clean(data.nombre_completo):
        errors["nombre_completo"] = "required"

    identification = _clean(data.numero_identificacion)
    if identification.isdigit() and len(identification) == CEDULA_LENGTH:
        cedula = cedula_error(identification)
        if cedula is not None:
            errors["numero_identificacion"] = f"cedula.{cedula.value}"

    for field, value in (
        ("telefono_principal", data.telefono_principal),
        ("telefono_secundario", data.telefono_secundario),
    ):
        phone = _clean(value)
        if phone:
            problem = phone_error(phone)
            if problem is not None:
                errors[field] = f"phone.{problem.value}"

    email = _clean(data.correo_electronico)
    if email and not email_is_valid(email):
        errors["correo_electronico"] = "email.invalid"
    return errors


def save_customer(session: Session, data: CustomerData, customer_id: int | None = None) -> Customer:
    """Crea o actualiza un cliente. Lanza CustomerValidationError si los datos no son válidos."""
    errors = customer_input_errors(data)
    if errors:
        raise CustomerValidationError(errors)

    if customer_id is None:
        customer = Customer()
        session.add(customer)
    else:
        found = session.get(Customer, customer_id)
        if found is None:
            raise ValueError("Cliente no encontrado.")
        customer = found

    customer.nombre_completo = _clean(data.nombre_completo)
    customer.numero_identificacion = _none_if_empty(data.numero_identificacion)
    customer.telefono_principal = _none_if_empty(data.telefono_principal)
    customer.telefono_secundario = _none_if_empty(data.telefono_secundario)
    customer.correo_electronico = _none_if_empty(data.correo_electronico)
    customer.direccion = _none_if_empty(data.direccion)
    customer.notas = _none_if_empty(data.notas)
    session.flush()
    return customer


def find_possible_duplicates(
    session: Session,
    numero_identificacion: str | None = None,
    telefono: str | None = None,
) -> list[Customer]:
    """Clientes que coinciden por identificación exacta o por teléfono sin formato.

    El teléfono se compara solo con sus dígitos, así "099 123-4567" coincide con "0991234567".
    """
    identification = _clean(numero_identificacion)
    phone = _digits(telefono)
    if len(phone) < MIN_PHONE_DIGITS:
        phone = ""
    if not identification and not phone:
        return []

    matches: list[Customer] = []
    for customer in session.scalars(select(Customer).order_by(Customer.id)):
        same_identification = bool(identification) and (
            _clean(customer.numero_identificacion) == identification
        )
        same_phone = bool(phone) and phone in {
            _digits(customer.telefono_principal),
            _digits(customer.telefono_secundario),
        }
        if same_identification or same_phone:
            matches.append(customer)
    return matches


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _none_if_empty(value: str | None) -> str | None:
    cleaned = _clean(value)
    return cleaned or None


def _digits(value: str | None) -> str:
    return "".join(char for char in (value or "") if char in "0123456789")
