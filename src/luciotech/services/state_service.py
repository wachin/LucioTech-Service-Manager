"""Cambio de estado de órdenes con registro automático en el historial (§5.5)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from luciotech.database.enums import OrderState
from luciotech.database.models import ServiceOrder, StateHistory


def change_order_state(
    session: Session,
    order: ServiceOrder,
    nuevo_estado: OrderState | str,
    usuario: str,
    comentario: str | None = None,
) -> StateHistory | None:
    """Cambia el estado y devuelve el registro de historial creado.

    Devuelve None si el estado no cambia, para no registrar cambios vacíos.
    """
    nuevo = OrderState(nuevo_estado)
    if order.estado == nuevo.value:
        return None

    anterior = order.estado
    order.estado = nuevo.value
    entry = StateHistory(
        order=order,
        estado_anterior=anterior,
        estado_nuevo=nuevo.value,
        comentario=comentario,
        usuario=usuario,
    )
    session.add(entry)
    session.flush()
    return entry
