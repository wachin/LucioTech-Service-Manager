"""Conteos del panel de inicio (§6). Solo cuentan órdenes activas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from luciotech.database.enums import OrderState, PaymentType
from luciotech.database.models import Payment, ServiceOrder

CENT = Decimal("0.01")


@dataclass(frozen=True)
class DashboardCounts:
    received_today: int
    pending_diagnosis: int
    under_repair: int
    awaiting_approval: int
    ready_for_delivery: int
    delivered_this_month: int
    outstanding_balance: Decimal
    monthly_income: Decimal


def dashboard_counts(session: Session, today: date) -> DashboardCounts:
    day_start = datetime.combine(today, time.min)
    day_end = day_start + timedelta(days=1)
    month_start = day_start.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)

    return DashboardCounts(
        received_today=_count_orders(
            session,
            ServiceOrder.fecha_ingreso >= day_start,
            ServiceOrder.fecha_ingreso < day_end,
        ),
        pending_diagnosis=_count_state(session, OrderState.PENDIENTE_DIAGNOSTICO),
        under_repair=_count_state(session, OrderState.EN_REPARACION),
        awaiting_approval=_count_state(session, OrderState.ESPERANDO_APROBACION),
        ready_for_delivery=_count_state(session, OrderState.LISTO_PARA_ENTREGAR),
        delivered_this_month=_count_orders(
            session,
            ServiceOrder.estado == OrderState.ENTREGADO.value,
            ServiceOrder.fecha_entrega >= month_start,
            ServiceOrder.fecha_entrega < next_month,
        ),
        outstanding_balance=_outstanding_balance(session),
        monthly_income=_monthly_income(session, month_start, next_month),
    )


def _count_orders(session: Session, *conditions: Any) -> int:
    statement = (
        select(func.count())
        .select_from(ServiceOrder)
        .where(ServiceOrder.activo.is_(True), *conditions)
    )
    return int(session.scalar(statement) or 0)


def _count_state(session: Session, state: OrderState) -> int:
    return _count_orders(session, ServiceOrder.estado == state.value)


def _outstanding_balance(session: Session) -> Decimal:
    statement = select(func.coalesce(func.sum(ServiceOrder.saldo_pendiente), 0)).where(
        ServiceOrder.activo.is_(True),
        ServiceOrder.estado != OrderState.CANCELADO.value,
    )
    return _money(session.scalar(statement))


def _monthly_income(session: Session, start: datetime, end: datetime) -> Decimal:
    is_refund = Payment.tipo_pago == PaymentType.REEMBOLSO.value
    statement = select(
        func.coalesce(func.sum(Payment.monto).filter(~is_refund), 0)
        - func.coalesce(func.sum(Payment.monto).filter(is_refund), 0)
    ).where(Payment.fecha >= start, Payment.fecha < end)
    return _money(session.scalar(statement))


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)
