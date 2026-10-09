"""Numeración atómica de órdenes con formato OT-AAAA-NNNNNN (§5.3)."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from luciotech.database.models import NumberSequence

ORDER_PREFIX = "OT"


def peek_next_order_number(session: Session, year: int) -> str:
    """Muestra el número que tendría la próxima orden, sin reservarlo."""
    key = f"{ORDER_PREFIX}-{year}"
    current = session.scalar(select(NumberSequence.ultimo_valor).where(NumberSequence.clave == key))
    return f"{key}-{(current or 0) + 1:06d}"


def next_order_number(session: Session, year: int) -> str:
    """Reserva el siguiente número del año dentro de la transacción actual.

    Si la transacción se revierte, el número también se libera, así no quedan huecos.
    """
    key = f"{ORDER_PREFIX}-{year}"
    session.execute(
        insert(NumberSequence)
        .values(clave=key, ultimo_valor=0)
        .on_conflict_do_nothing(index_elements=["clave"])
    )
    session.execute(
        update(NumberSequence)
        .where(NumberSequence.clave == key)
        .values(ultimo_valor=NumberSequence.ultimo_valor + 1)
    )
    value = session.scalar(select(NumberSequence.ultimo_valor).where(NumberSequence.clave == key))
    return f"{key}-{value:06d}"
