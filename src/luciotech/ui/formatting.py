"""Formatos de fecha e importe para la interfaz."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from luciotech.config import DEFAULT_CURRENCY

DATETIME_FORMAT = "%d/%m/%Y %H:%M"


def format_money(amount: Decimal | None) -> str:
    value = amount if amount is not None else Decimal("0")
    return f"{value:,.2f} {DEFAULT_CURRENCY}"


def format_datetime(value: datetime | None) -> str:
    return value.strftime(DATETIME_FORMAT) if value else ""
