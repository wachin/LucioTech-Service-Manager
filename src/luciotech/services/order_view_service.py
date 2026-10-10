"""Datos de las pestañas Cliente y Equipo de la vista de orden (§9 del ROADMAP)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from luciotech.database.enums import OrderState
from luciotech.database.models import ServiceOrder


@dataclass(frozen=True)
class CustomerView:
    nombre_completo: str
    numero_identificacion: str
    telefono_principal: str
    telefono_secundario: str
    correo_electronico: str
    direccion: str
    notas: str
    otras_ordenes: list[str]
    saldo_pendiente_total: Decimal


@dataclass(frozen=True)
class EquipmentView:
    tipo_equipo: str
    marca: str
    modelo: str
    numero_serie: str
    color: str
    sistema_operativo: str
    contrasena_equipo: str
    accesorios_recibidos: str
    estado_fisico: str
    problema_reportado_cliente: str
    observaciones_ingreso: str


def customer_view(session: Session, order: ServiceOrder) -> CustomerView:
    """Datos del cliente, sus otras órdenes activas y el saldo pendiente total."""
    customer = order.customer
    others = session.scalars(
        select(ServiceOrder)
        .where(
            ServiceOrder.cliente_id == customer.id,
            ServiceOrder.activo.is_(True),
            ServiceOrder.id != order.id,
        )
        .order_by(ServiceOrder.fecha_ingreso.desc())
    ).all()
    balance = sum(
        (o.saldo_pendiente for o in [order, *others] if o.estado != OrderState.CANCELADO.value),
        Decimal("0.00"),
    )
    return CustomerView(
        nombre_completo=customer.nombre_completo,
        numero_identificacion=customer.numero_identificacion or "",
        telefono_principal=customer.telefono_principal or "",
        telefono_secundario=customer.telefono_secundario or "",
        correo_electronico=customer.correo_electronico or "",
        direccion=customer.direccion or "",
        notas=customer.notas or "",
        otras_ordenes=[o.numero_orden for o in others],
        saldo_pendiente_total=balance,
    )


def equipment_view(order: ServiceOrder) -> EquipmentView:
    """Datos técnicos del equipo asociado a la orden. La contraseña se devuelve tal cual; la UI la oculta."""
    equipment = order.equipment
    return EquipmentView(
        tipo_equipo=equipment.tipo_equipo,
        marca=equipment.marca or "",
        modelo=equipment.modelo or "",
        numero_serie=equipment.numero_serie or "",
        color=equipment.color or "",
        sistema_operativo=equipment.sistema_operativo or "",
        contrasena_equipo=equipment.contrasena_equipo or "",
        accesorios_recibidos=equipment.accesorios_recibidos or "",
        estado_fisico=equipment.estado_fisico or "",
        problema_reportado_cliente=equipment.problema_reportado_cliente or "",
        observaciones_ingreso=equipment.observaciones_ingreso or "",
    )
