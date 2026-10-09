"""Consultas de equipos para advertencias de duplicados (§7.2)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from luciotech.database.models import Equipment, ServiceOrder


def find_orders_with_serial(session: Session, numero_serie: str | None) -> list[ServiceOrder]:
    """Órdenes activas cuyo equipo tiene ese número de serie (sin distinguir mayúsculas).

    La coincidencia es solo una advertencia: no debe bloquear el guardado.
    """
    serial = (numero_serie or "").strip().upper()
    if not serial:
        return []
    statement = (
        select(ServiceOrder)
        .join(ServiceOrder.equipment)
        .where(func.upper(Equipment.numero_serie) == serial)
        .where(ServiceOrder.activo.is_(True))
        .order_by(ServiceOrder.fecha_ingreso.desc())
    )
    return list(session.scalars(statement))
