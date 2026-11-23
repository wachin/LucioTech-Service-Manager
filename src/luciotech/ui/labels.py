"""Etiquetas traducidas de los valores que la base guarda en español.

La base de datos conserva los valores del dominio tal como se crearon («Recibido»,
«Efectivo», «Administrador»…): cambiarlos obligaría a migrar todas las órdenes y los
historiales existentes. La interfaz no los enseña en crudo, sino que los pasa por aquí
para que `QTranslator` los muestre en el idioma elegido.
"""

from __future__ import annotations

from collections.abc import Mapping

from PyQt6.QtCore import QCoreApplication

from luciotech.database.enums import (
    BudgetLineType,
    EventType,
    OrderState,
    PaymentMethod,
    PaymentType,
    PhotoType,
    Priority,
    UserRole,
)

_CONTEXT = "LucioTech"

_STATES: dict[str, str] = {
    OrderState.RECIBIDO.value: "Received",
    OrderState.PENDIENTE_DIAGNOSTICO.value: "Pending diagnosis",
    OrderState.DIAGNOSTICADO.value: "Diagnosed",
    OrderState.ESPERANDO_APROBACION.value: "Awaiting approval",
    OrderState.ESPERANDO_REPUESTO.value: "Waiting for parts",
    OrderState.EN_REPARACION.value: "Under repair",
    OrderState.REPARADO.value: "Repaired",
    OrderState.LISTO_PARA_ENTREGAR.value: "Ready for delivery",
    OrderState.ENTREGADO.value: "Delivered",
    OrderState.NO_REPARABLE.value: "Not repairable",
    OrderState.CANCELADO.value: "Cancelled",
}

_PRIORITIES: dict[str, str] = {
    Priority.BAJA.value: "Low",
    Priority.NORMAL.value: "Normal",
    Priority.ALTA.value: "High",
    Priority.URGENTE.value: "Urgent",
}

_PHOTO_TYPES: dict[str, str] = {
    PhotoType.ESTADO_AL_RECIBIR.value: "Condition on arrival",
    PhotoType.NUMERO_DE_SERIE.value: "Serial number",
    PhotoType.ACCESORIOS.value: "Accessories",
    PhotoType.DANO_FISICO.value: "Physical damage",
    PhotoType.PROCESO_DE_REPARACION.value: "Repair in progress",
    PhotoType.EQUIPO_REPARADO.value: "Repaired equipment",
    PhotoType.OTRO.value: "Other",
}

_PAYMENT_TYPES: dict[str, str] = {
    PaymentType.ANTICIPO.value: "Deposit",
    PaymentType.ABONO.value: "Part payment",
    PaymentType.PAGO_FINAL.value: "Final payment",
    PaymentType.REEMBOLSO.value: "Refund",
}

_PAYMENT_METHODS: dict[str, str] = {
    PaymentMethod.EFECTIVO.value: "Cash",
    PaymentMethod.TRANSFERENCIA.value: "Bank transfer",
    PaymentMethod.TARJETA.value: "Card",
    PaymentMethod.DEPOSITO.value: "Bank deposit",
    PaymentMethod.OTRO.value: "Other",
}

_ROLES: dict[str, str] = {
    UserRole.ADMINISTRADOR.value: "Administrator",
    UserRole.TECNICO.value: "Technician",
}

_BUDGET_LINE_TYPES: dict[str, str] = {
    BudgetLineType.DIAGNOSTICO.value: "Diagnosis",
    BudgetLineType.MANO_OBRA.value: "Labour",
    BudgetLineType.REPUESTO.value: "Part",
    BudgetLineType.ACCESORIO.value: "Accessory",
    BudgetLineType.SERVICIO.value: "Service",
    BudgetLineType.OTRO.value: "Other",
}

_EQUIPMENT_TYPES: dict[str, str] = {
    "Laptop": "Laptop",
    "Computadora de escritorio": "Desktop computer",
    "Impresora": "Printer",
    "Cámara de seguridad": "Security camera",
    "DVR": "DVR",
    "NVR": "NVR",
    "Monitor": "Monitor",
    "Router": "Router",
    "Fuente de poder": "Power supply",
    "Otro": "Other",
}

_ACCESSORIES: dict[str, str] = {
    "Fuente de alimentación": "Power supply",
    "Adaptador": "Adapter",
    "Cable": "Cable",
    "Disco duro": "Hard drive",
    "Control remoto": "Remote control",
    "Mouse": "Mouse",
    "Antena": "Antenna",
    "Cargador": "Charger",
    "Batería": "Battery",
    "Bolso": "Bag",
    "Memoria USB": "USB drive",
    "Cable de corriente": "Power cable",
    "Monitor": "Monitor",
    "Teclado": "Keyboard",
    "Parlantes": "Speakers",
    "Adaptador Wi-Fi": "Wi-Fi adapter",
    "Cable USB": "USB cable",
    "Cartuchos": "Cartridges",
    "Botellas de tinta": "Ink bottles",
    "Bandejas": "Trays",
    "Otro": "Other",
}

_GENERATED_DETAILS: dict[str, str] = {
    "Orden creada": "Order created",
}

_EVENT_TITLES: dict[str, str] = {
    EventType.LLAMADA_CLIENTE.value: "Call to customer",
    EventType.MENSAJE_ENVIADO.value: "Message sent",
    EventType.PRESUPUESTO_APROBADO.value: "Budget approved",
    EventType.PRESUPUESTO_RECHAZADO.value: "Budget rejected",
    EventType.REPUESTO_SOLICITADO.value: "Part requested",
    EventType.REPUESTO_RECIBIDO.value: "Part received",
    EventType.DIAGNOSTICO_ACTUALIZADO.value: "Diagnosis updated",
    EventType.PAGO_RECIBIDO.value: "Payment received",
    EventType.PAGO_ANULADO.value: "Payment voided",
    EventType.EQUIPO_ENTREGADO.value: "Equipment delivered",
    EventType.NOTA_INTERNA.value: "Internal note",
    EventType.ORDEN_ELIMINADA.value: "Order deleted",
    EventType.ORDEN_RESTAURADA.value: "Order restored",
    "Cambio de estado": "State change",
    "Equipo entregado al cliente": "Equipment delivered to the customer",
}


def _label(mapping: Mapping[str, str], value: str | None) -> str:
    source = mapping.get(str(value or ""))
    if source is None:
        return str(value or "")
    return QCoreApplication.translate("LucioTech", source)


def equipment_type_label(value: str | None) -> str:
    """Tipo de equipo para mostrar; el valor guardado sigue siendo el original."""
    return _label(_EQUIPMENT_TYPES, value)


def accessory_label(value: str | None) -> str:
    """Accesorio sugerido para mostrar; la selección se sigue guardando en español."""
    return _label(_ACCESSORIES, value)


def equipment_type_value(label: str | None) -> str:
    """Vuelve del texto mostrado al valor que se guarda (para el editor de Configuración)."""
    text = str(label or "").strip()
    for value, source in _EQUIPMENT_TYPES.items():
        if text in (value, source, QCoreApplication.translate("LucioTech", source)):
            return value
    return text


def state_label(value: str | None) -> str:
    return _label(_STATES, value)


def priority_label(value: str | None) -> str:
    return _label(_PRIORITIES, value)


def photo_type_label(value: str | None) -> str:
    return _label(_PHOTO_TYPES, value)


def payment_type_label(value: str | None) -> str:
    return _label(_PAYMENT_TYPES, value)


def payment_method_label(value: str | None) -> str:
    return _label(_PAYMENT_METHODS, value)


def role_label(value: str | None) -> str:
    return _label(_ROLES, value)


def budget_line_type_label(value: str | None) -> str:
    return _label(_BUDGET_LINE_TYPES, value)


def event_title_label(value: str | None) -> str:
    """Título de un evento; también traduce los pagos («Anticipo de 10.00»)."""
    text = str(value or "")
    fixed = _EVENT_TITLES.get(text)
    if fixed is not None:
        return QCoreApplication.translate("LucioTech", fixed)
    for kind, source in _PAYMENT_TYPES.items():
        if text.startswith(f"{kind} de "):
            amount = text[len(kind) + len(" de ") :]
            return _t_source("Payment event").format(
                type=QCoreApplication.translate("LucioTech", source), amount=amount
            )
    return text


def _t_source(source: str) -> str:
    return QCoreApplication.translate("LucioTech", source)


def history_detail_label(detail: str) -> str:
    """Traduce los estados y los comentarios que genera el programa en el historial."""
    text = detail
    for value, source in _GENERATED_DETAILS.items():
        if value in text:
            text = text.replace(value, QCoreApplication.translate("LucioTech", source))
    for value, source in _STATES.items():
        if value in text:
            text = text.replace(value, QCoreApplication.translate("LucioTech", source))
    return text


def _catalog() -> None:
    """Mantiene los textos en el catálogo de pylupdate6; no se ejecuta nunca.

    Las etiquetas se traducen al usarlas, así que la extracción no puede ver sus literales.
    """
    QCoreApplication.translate("LucioTech", 'Received')
    QCoreApplication.translate("LucioTech", 'Pending diagnosis')
    QCoreApplication.translate("LucioTech", 'Diagnosed')
    QCoreApplication.translate("LucioTech", 'Awaiting approval')
    QCoreApplication.translate("LucioTech", 'Waiting for parts')
    QCoreApplication.translate("LucioTech", 'Under repair')
    QCoreApplication.translate("LucioTech", 'Repaired')
    QCoreApplication.translate("LucioTech", 'Ready for delivery')
    QCoreApplication.translate("LucioTech", 'Delivered')
    QCoreApplication.translate("LucioTech", 'Not repairable')
    QCoreApplication.translate("LucioTech", 'Cancelled')
    QCoreApplication.translate("LucioTech", 'Low')
    QCoreApplication.translate("LucioTech", 'Normal')
    QCoreApplication.translate("LucioTech", 'High')
    QCoreApplication.translate("LucioTech", 'Urgent')
    QCoreApplication.translate("LucioTech", 'Condition on arrival')
    QCoreApplication.translate("LucioTech", 'Serial number')
    QCoreApplication.translate("LucioTech", 'Accessories')
    QCoreApplication.translate("LucioTech", 'Physical damage')
    QCoreApplication.translate("LucioTech", 'Repair in progress')
    QCoreApplication.translate("LucioTech", 'Repaired equipment')
    QCoreApplication.translate("LucioTech", 'Other')
    QCoreApplication.translate("LucioTech", 'Deposit')
    QCoreApplication.translate("LucioTech", 'Part payment')
    QCoreApplication.translate("LucioTech", 'Final payment')
    QCoreApplication.translate("LucioTech", 'Refund')
    QCoreApplication.translate("LucioTech", 'Cash')
    QCoreApplication.translate("LucioTech", 'Bank transfer')
    QCoreApplication.translate("LucioTech", 'Card')
    QCoreApplication.translate("LucioTech", 'Bank deposit')
    QCoreApplication.translate("LucioTech", 'Administrator')
    QCoreApplication.translate("LucioTech", 'Technician')
    QCoreApplication.translate("LucioTech", 'Diagnosis')
    QCoreApplication.translate("LucioTech", 'Labour')
    QCoreApplication.translate("LucioTech", 'Part')
    QCoreApplication.translate("LucioTech", 'Accessory')
    QCoreApplication.translate("LucioTech", 'Service')
    QCoreApplication.translate("LucioTech", 'Call to customer')
    QCoreApplication.translate("LucioTech", 'Message sent')
    QCoreApplication.translate("LucioTech", 'Budget approved')
    QCoreApplication.translate("LucioTech", 'Budget rejected')
    QCoreApplication.translate("LucioTech", 'Part requested')
    QCoreApplication.translate("LucioTech", 'Part received')
    QCoreApplication.translate("LucioTech", 'Diagnosis updated')
    QCoreApplication.translate("LucioTech", 'Payment received')
    QCoreApplication.translate("LucioTech", 'Payment voided')
    QCoreApplication.translate("LucioTech", 'Equipment delivered')
    QCoreApplication.translate("LucioTech", 'Internal note')
    QCoreApplication.translate("LucioTech", 'Order deleted')
    QCoreApplication.translate("LucioTech", 'Order restored')
    QCoreApplication.translate("LucioTech", 'State change')
    QCoreApplication.translate("LucioTech", 'Equipment delivered to the customer')
    QCoreApplication.translate("LucioTech", "Laptop")
    QCoreApplication.translate("LucioTech", "Desktop computer")
    QCoreApplication.translate("LucioTech", "Printer")
    QCoreApplication.translate("LucioTech", "Security camera")
    QCoreApplication.translate("LucioTech", "DVR")
    QCoreApplication.translate("LucioTech", "NVR")
    QCoreApplication.translate("LucioTech", "Monitor")
    QCoreApplication.translate("LucioTech", "Router")
    QCoreApplication.translate("LucioTech", "Power supply")
    QCoreApplication.translate("LucioTech", "Power supply")
    QCoreApplication.translate("LucioTech", "Adapter")
    QCoreApplication.translate("LucioTech", "Cable")
    QCoreApplication.translate("LucioTech", "Hard drive")
    QCoreApplication.translate("LucioTech", "Remote control")
    QCoreApplication.translate("LucioTech", "Antenna")
    QCoreApplication.translate("LucioTech", "Charger")
    QCoreApplication.translate("LucioTech", "Battery")
    QCoreApplication.translate("LucioTech", "Bag")
    QCoreApplication.translate("LucioTech", "USB drive")
    QCoreApplication.translate("LucioTech", "Power cable")
    QCoreApplication.translate("LucioTech", "Keyboard")
    QCoreApplication.translate("LucioTech", "Speakers")
    QCoreApplication.translate("LucioTech", "Wi-Fi adapter")
    QCoreApplication.translate("LucioTech", "USB cable")
    QCoreApplication.translate("LucioTech", "Cartridges")
    QCoreApplication.translate("LucioTech", "Ink bottles")
    QCoreApplication.translate("LucioTech", "Trays")
    QCoreApplication.translate("LucioTech", "Order created")
