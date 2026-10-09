"""Detección de clientes posiblemente duplicados por identificación o teléfono (§7.1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from luciotech.database.models import Customer

MIN_PHONE_DIGITS = 7


def find_possible_duplicates(
    session: Session,
    numero_identificacion: str | None = None,
    telefono: str | None = None,
) -> list[Customer]:
    """Clientes que coinciden por identificación exacta o por teléfono sin formato.

    El teléfono se compara solo con sus dígitos, así "099 123-4567" coincide con "0991234567".
    """
    identification = (numero_identificacion or "").strip()
    phone = _digits(telefono)
    if phone and len(phone) < MIN_PHONE_DIGITS:
        phone = ""
    if not identification and not phone:
        return []

    matches: list[Customer] = []
    for customer in session.scalars(select(Customer).order_by(Customer.id)):
        same_identification = bool(identification) and (
            (customer.numero_identificacion or "").strip() == identification
        )
        same_phone = bool(phone) and phone in {
            _digits(customer.telefono_principal),
            _digits(customer.telefono_secundario),
        }
        if same_identification or same_phone:
            matches.append(customer)
    return matches


def _digits(value: str | None) -> str:
    return "".join(char for char in (value or "") if char.isdigit())
