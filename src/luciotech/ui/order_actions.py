"""Siguiente paso de una orden según su estado (§9).

El técnico no debería tener que recordar qué toca después de cada cambio. Cada estado propone
una sola acción principal, y la ventana de la orden la ofrece como botón grande en el resumen.
Las transiciones siguen siendo libres (el ROADMAP aún no fija reglas, §5.6), así que esto es
una sugerencia: el selector «Cambiar estado» sigue estando para cualquier salto.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QCoreApplication

from luciotech.database.enums import OrderState
from luciotech.ui.documents import DocumentKind


@dataclass(frozen=True)
class NextAction:
    """Acción que la ventana de la orden ofrece como «siguiente paso»."""

    label: str
    hint: str = ""
    state: OrderState | None = None
    document: DocumentKind | None = None
    delivers: bool = False

    @property
    def available(self) -> bool:
        """True si pulsar el botón hace algo (cambiar de estado, entregar o abrir un papel)."""
        return self.state is not None or self.delivers or self.document is not None


NEXT_ACTIONS: dict[OrderState, NextAction] = {
    OrderState.RECIBIDO: NextAction(
        label="Start diagnosis",
        hint="The equipment is already in the workshop: move it to the diagnosis queue.",
        state=OrderState.PENDIENTE_DIAGNOSTICO,
    ),
    OrderState.PENDIENTE_DIAGNOSTICO: NextAction(
        label="Mark as diagnosed",
        hint="Write the diagnosis on the Work tab first.",
        state=OrderState.DIAGNOSTICADO,
    ),
    OrderState.DIAGNOSTICADO: NextAction(
        label="Give the budget to the customer",
        hint="The order awaits approval and the budget opens for printing.",
        state=OrderState.ESPERANDO_APROBACION,
        document=DocumentKind.PRESUPUESTO,
    ),
    OrderState.ESPERANDO_APROBACION: NextAction(
        label="Start the repair",
        hint="With the budget approved, start working on the equipment.",
        state=OrderState.EN_REPARACION,
    ),
    OrderState.ESPERANDO_REPUESTO: NextAction(
        label="Resume the repair",
        hint="The part has arrived: get back to work on the equipment.",
        state=OrderState.EN_REPARACION,
    ),
    OrderState.EN_REPARACION: NextAction(
        label="Mark as repaired",
        hint="When the equipment works, mark it and hand over the technical report.",
        state=OrderState.REPARADO,
        document=DocumentKind.INFORME,
    ),
    OrderState.REPARADO: NextAction(
        label="Ready for delivery",
        hint="Tell the customer the equipment is ready to be collected.",
        state=OrderState.LISTO_PARA_ENTREGAR,
    ),
    OrderState.LISTO_PARA_ENTREGAR: NextAction(
        label="Deliver the equipment",
        hint="Collect any balance due and hand over the receipt with the delivery date.",
        delivers=True,
        document=DocumentKind.ENTREGA,
    ),
    OrderState.ENTREGADO: NextAction(
        label="Print the delivery receipt",
        hint="The order is closed: reprint the receipt whenever needed.",
        document=DocumentKind.ENTREGA,
    ),
    OrderState.NO_REPARABLE: NextAction(
        label="Print the technical report",
        hint="The equipment cannot be repaired: hand over the report and return it.",
        document=DocumentKind.INFORME,
    ),
    OrderState.CANCELADO: NextAction(
        label="No pending actions",
        hint="The order is cancelled: only the history remains.",
    ),
}

FALLBACK = NextAction(label="No pending actions")


def next_action(state: OrderState | str) -> NextAction:
    """Acción propuesta para ese estado; si el valor no se reconoce, una neutra."""
    try:
        return NEXT_ACTIONS[OrderState(state)]
    except ValueError:
        return FALLBACK


def _catalog() -> None:
    """Mantiene los textos en el catálogo de pylupdate6; no se ejecuta nunca."""
    QCoreApplication.translate("NextAction", 'No pending actions')
    QCoreApplication.translate("NextAction", 'Start diagnosis')
    QCoreApplication.translate("NextAction", 'The equipment is already in the workshop: move it to the diagnosis queue.')
    QCoreApplication.translate("NextAction", 'Mark as diagnosed')
    QCoreApplication.translate("NextAction", 'Write the diagnosis on the Work tab first.')
    QCoreApplication.translate("NextAction", 'Give the budget to the customer')
    QCoreApplication.translate("NextAction", 'The order awaits approval and the budget opens for printing.')
    QCoreApplication.translate("NextAction", 'Start the repair')
    QCoreApplication.translate("NextAction", 'With the budget approved, start working on the equipment.')
    QCoreApplication.translate("NextAction", 'Resume the repair')
    QCoreApplication.translate("NextAction", 'The part has arrived: get back to work on the equipment.')
    QCoreApplication.translate("NextAction", 'Mark as repaired')
    QCoreApplication.translate("NextAction", 'When the equipment works, mark it and hand over the technical report.')
    QCoreApplication.translate("NextAction", 'Ready for delivery')
    QCoreApplication.translate("NextAction", 'Tell the customer the equipment is ready to be collected.')
    QCoreApplication.translate("NextAction", 'Deliver the equipment')
    QCoreApplication.translate("NextAction", 'Collect any balance due and hand over the receipt with the delivery date.')
    QCoreApplication.translate("NextAction", 'Print the delivery receipt')
    QCoreApplication.translate("NextAction", 'The order is closed: reprint the receipt whenever needed.')
    QCoreApplication.translate("NextAction", 'Print the technical report')
    QCoreApplication.translate("NextAction", 'The equipment cannot be repaired: hand over the report and return it.')
    QCoreApplication.translate("NextAction", 'The order is cancelled: only the history remains.')
