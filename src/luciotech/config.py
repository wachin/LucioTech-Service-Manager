"""Configuración centralizada de la aplicación (§1 y §2 del ROADMAP).

Cambiar el nombre, el app_id o la versión se hace únicamente aquí.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AppConfig:
    """Valores fijos de identidad de la aplicación."""

    app_name: str
    app_id: str
    organization_name: str
    application_version: str
    executable_name: str


APP_CONFIG = AppConfig(
    app_name="LucioTech Service Manager",
    app_id="luciotech-service-manager",
    organization_name="Ing. Lucio",
    application_version="0.1.0",
    executable_name="luciotech-service-manager",
)

APP_VERSION: str = APP_CONFIG.application_version

# Idioma con el que arranca la aplicación: el español del taller. El inglés es el idioma
# fuente del código; cada traducción vive en su archivo `.ts`/`.qm` (§21).
DEFAULT_LANGUAGE = "es"

DEFAULT_TAX_PERCENT = Decimal("15")
# El taller trabaja con precios que ya llevan el IVA incluido, así que el impuesto nace
# desactivado: el total es el subtotal. Sigue siendo configurable (§5.8) y el porcentaje se
# conserva para cuando se quiera volver a sumarlo.
DEFAULT_TAX_ENABLED = False
DEFAULT_CURRENCY = "USD"
DEFAULT_USER = "Ing. Lucio"

# Meses que se considera abandonado un equipo sin retirar antes de poder darlo de baja (§5.8).
DEFAULT_RETENTION_MONTHS = 6

# Días que un presupuesto impreso mantiene su validez (§13.1.3).
DEFAULT_BUDGET_VALIDITY_DAYS = 15

# Hoja y márgenes con los que salen los documentos (§13.2). «Carta» es el tamaño Letter.
DEFAULT_PAPER_SIZE = "A4"
PAPER_SIZES: tuple[str, ...] = ("A4", "Carta")
DEFAULT_PAGE_MARGIN_MM = 15
MIN_PAGE_MARGIN_MM = 5
MAX_PAGE_MARGIN_MM = 40

# English is the source language: these defaults are translated when they are shown (§21).
# The {meses} placeholder is replaced by the configured deadline when printing.
DEFAULT_SERVICE_TERMS = (
    "1. The repair starts only with the budget approved by the customer.\n"
    "2. The repaired equipment is covered by a warranty on the work performed.\n"
    "3. If the equipment is not collected within {meses} months from the date of receipt, it "
    "will be considered abandoned and the workshop may dispose of it."
)

# Días de garantía que recibe cada orden nueva; se cambia en la pantalla de Configuración.
DEFAULT_WARRANTY_DAYS = 30

# Minutos sin teclado ni ratón antes de que la ventana principal pida la contraseña de la
# sesión otra vez. La cuenta de respaldo sin sesión (DEFAULT_CURRENT_USER) no se bloquea.
INACTIVITY_LOCK_MINUTES = 10

# The {dias}, {orden} and {meses} placeholders are replaced when printing (§13.1.2 and §13.1.4).
DEFAULT_WARRANTY_TERMS = (
    "1. The warranty covers the work performed and the parts invoiced for {dias} days from "
    "the delivery of the equipment.\n"
    "2. It does not cover damage from knocks, liquids, electrical surges, software installed "
    "by the customer or third-party work.\n"
    "3. To claim the warranty, the customer must present this document with order {orden}."
)

DEFAULT_PREDEFINED_TEXTS: tuple[str, ...] = (
    "A visual inspection of the equipment was performed.",
    "Power-on tests were performed.",
    "The storage condition was checked.",
    "The RAM was checked.",
    "Preventive maintenance is recommended.",
    "Replacing the faulty component is recommended.",
    "The equipment was tested and works correctly.",
)

# Los tipos de equipo son datos editables del taller y se guardan tal cual; la interfaz los
# muestra traducidos con `ui/labels.py`.
DEFAULT_EQUIPMENT_TYPES: tuple[str, ...] = (
    "Laptop",
    "Computadora de escritorio",
    "Impresora",
    "Cámara de seguridad",
    "DVR",
    "NVR",
    "Monitor",
    "Router",
    "Fuente de poder",
    "Otro",
)
