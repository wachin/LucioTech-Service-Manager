"""Lectura y escritura de la configuración de negocio (tabla configuracion, §5.8)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from luciotech.config import DEFAULT_EQUIPMENT_TYPES, DEFAULT_TAX_ENABLED, DEFAULT_TAX_PERCENT
from luciotech.database.models import Configuration

KEY_TAX_PERCENT = "impuesto_porcentaje"
KEY_TAX_ENABLED = "impuesto_activo"
KEY_EQUIPMENT_TYPES = "tipos_equipo"


@dataclass(frozen=True)
class TaxSettings:
    percent: Decimal
    enabled: bool


def get_value(session: Session, clave: str, default: str | None = None) -> str | None:
    row = session.scalar(select(Configuration).where(Configuration.clave == clave))
    if row is None or row.valor is None:
        return default
    return row.valor


def set_value(session: Session, clave: str, valor: str) -> None:
    row = session.scalar(select(Configuration).where(Configuration.clave == clave))
    if row is None:
        session.add(Configuration(clave=clave, valor=valor))
    else:
        row.valor = valor
    session.flush()


def equipment_types(session: Session) -> list[str]:
    """Tipos de equipo: uno por línea en la configuración, o los valores por defecto."""
    raw = get_value(session, KEY_EQUIPMENT_TYPES)
    if raw is None:
        return list(DEFAULT_EQUIPMENT_TYPES)
    items = [line.strip() for line in raw.splitlines() if line.strip()]
    return items or list(DEFAULT_EQUIPMENT_TYPES)


def tax_settings(session: Session) -> TaxSettings:
    raw_percent = get_value(session, KEY_TAX_PERCENT, str(DEFAULT_TAX_PERCENT)) or ""
    try:
        percent = Decimal(raw_percent.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Porcentaje de impuesto no válido: {raw_percent!r}") from exc
    if not Decimal("0") <= percent <= Decimal("100"):
        raise ValueError("El porcentaje de impuesto debe estar entre 0 y 100.")

    raw_enabled = get_value(session, KEY_TAX_ENABLED, str(DEFAULT_TAX_ENABLED).lower()) or ""
    return TaxSettings(percent=percent, enabled=raw_enabled.strip().lower() == "true")
