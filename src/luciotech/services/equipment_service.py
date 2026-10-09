"""Equipos: validación, guardado y advertencia de número de serie repetido (§5.2, §7.2)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from luciotech.database.models import Customer, Equipment, ServiceOrder


class EquipmentValidationError(ValueError):
    """Lleva un diccionario campo -> código de error para que la UI lo muestre."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Datos de equipo no válidos.")
        self.errors = errors


@dataclass(frozen=True)
class EquipmentData:
    cliente_id: int | None
    tipo_equipo: str
    marca: str | None = None
    modelo: str | None = None
    numero_serie: str | None = None
    color: str | None = None
    sistema_operativo: str | None = None
    contrasena_equipo: str | None = None
    accesorios_recibidos: str | None = None
    estado_fisico: str | None = None
    problema_reportado_cliente: str | None = None
    observaciones_ingreso: str | None = None


def equipment_input_errors(data: EquipmentData, allowed_types: Sequence[str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if data.cliente_id is None:
        errors["cliente_id"] = "required"
    tipo = data.tipo_equipo.strip()
    if not tipo:
        errors["tipo_equipo"] = "required"
    elif tipo not in allowed_types:
        errors["tipo_equipo"] = "invalid_type"
    return errors


def save_equipment(
    session: Session,
    data: EquipmentData,
    allowed_types: Sequence[str],
    equipment_id: int | None = None,
) -> Equipment:
    """Crea o actualiza un equipo. La contraseña es opcional y nunca se registra en logs."""
    errors = equipment_input_errors(data, allowed_types)
    if data.cliente_id is not None and session.get(Customer, data.cliente_id) is None:
        errors["cliente_id"] = "not_found"
    if errors:
        raise EquipmentValidationError(errors)

    if equipment_id is None:
        equipment = Equipment()
        session.add(equipment)
    else:
        found = session.get(Equipment, equipment_id)
        if found is None:
            raise ValueError("Equipo no encontrado.")
        equipment = found

    equipment.cliente_id = data.cliente_id
    equipment.tipo_equipo = data.tipo_equipo.strip()
    equipment.marca = _none_if_empty(data.marca)
    equipment.modelo = _none_if_empty(data.modelo)
    equipment.numero_serie = _none_if_empty(data.numero_serie)
    equipment.color = _none_if_empty(data.color)
    equipment.sistema_operativo = _none_if_empty(data.sistema_operativo)
    equipment.contrasena_equipo = data.contrasena_equipo or None
    equipment.accesorios_recibidos = _none_if_empty(data.accesorios_recibidos)
    equipment.estado_fisico = _none_if_empty(data.estado_fisico)
    equipment.problema_reportado_cliente = _none_if_empty(data.problema_reportado_cliente)
    equipment.observaciones_ingreso = _none_if_empty(data.observaciones_ingreso)
    session.flush()
    return equipment


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


def _none_if_empty(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None
