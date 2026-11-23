"""Documentos imprimibles de una orden (§13.1).

Cinco documentos: comprobante de recepción, presupuesto, informe técnico, comprobante de
entrega e historial completo. Se arman como HTML y se imprimen con los diálogos de Qt
(§13.3). La contraseña del equipo nunca aparece: los documentos se entregan al cliente (§5.2).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt6.QtWidgets import QMessageBox, QWidget
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import DEFAULT_PAGE_MARGIN_MM, DEFAULT_PAPER_SIZE
from luciotech.database.enums import BudgetLineType, PhotoType
from luciotech.database.models import Photograph, ServiceOrder
from luciotech.services.order_detail_service import order_timeline, payments_for_order
from luciotech.services.settings_service import (
    budget_validity_days,
    effective_warranty_days,
    page_margin_mm,
    paper_size,
    service_conditions,
    tax_settings,
    warranty_conditions,
    workshop_contact,
    workshop_name,
)
from luciotech.services.totals_service import OrderTotals, order_totals
from luciotech.ui.formatting import format_datetime, format_money
from luciotech.ui.labels import (
    budget_line_type_label,
    equipment_type_label,
    event_title_label,
    history_detail_label,
    payment_method_label,
    payment_type_label,
    state_label,
)
from luciotech.ui.print_support import (
    PageFurniture,
    add_pdf_action,
    apply_page_setup,
    render_document,
    size_preview,
)

MAX_PHOTOS = 4
EMPTY = "—"
SIGNATURE = "____________________________"
ZERO = Decimal("0.00")
_CONTEXT = "LucioTech"
_BEFORE = (
    PhotoType.ESTADO_AL_RECIBIR,
    PhotoType.DANO_FISICO,
    PhotoType.ACCESORIOS,
    PhotoType.NUMERO_DE_SERIE,
)
_AFTER = (PhotoType.PROCESO_DE_REPARACION, PhotoType.EQUIPO_REPARADO)
_HEAD_CELL = "padding: 1pt 4pt; border-bottom: 1pt solid #000000;"
_CELL = "padding: 0.5pt 4pt; vertical-align: top;"
_RIGHT = " text-align: right;"


class DocumentKind(StrEnum):
    """Tipos de documento que se pueden imprimir de una orden (§13.1)."""

    RECEPCION = "Comprobante de recepción"
    PRESUPUESTO = "Presupuesto"
    INFORME = "Informe técnico"
    ENTREGA = "Comprobante de entrega"
    HISTORIAL = "Historial completo"

    @property
    def file_stem(self) -> str:
        """Parte descriptiva del nombre del PDF: «Informe-Tecnico» (§13.2)."""
        return _FILE_STEMS[self]


_DOCUMENT_SOURCES: dict[DocumentKind, str] = {
    DocumentKind.RECEPCION: "Reception receipt",
    DocumentKind.PRESUPUESTO: "Budget",
    DocumentKind.INFORME: "Technical report",
    DocumentKind.ENTREGA: "Delivery receipt",
    DocumentKind.HISTORIAL: "Full history",
}


def document_label(kind: DocumentKind | str) -> str:
    """Nombre traducido del documento; el valor guardado sigue siendo el español."""
    document = DocumentKind(kind)
    return QCoreApplication.translate("LucioTech", _DOCUMENT_SOURCES[document])


_FILE_STEMS: dict[DocumentKind, str] = {
    DocumentKind.RECEPCION: "Comprobante-Recepcion",
    DocumentKind.PRESUPUESTO: "Presupuesto",
    DocumentKind.INFORME: "Informe-Tecnico",
    DocumentKind.ENTREGA: "Comprobante-Entrega",
    DocumentKind.HISTORIAL: "Historial",
}


def pdf_filename(order: ServiceOrder, kind: DocumentKind | str) -> str:
    """Nombre descriptivo del PDF: «OT-2026-000001_Ana-Torres_Informe-Tecnico.pdf»."""
    document = DocumentKind(kind)
    return f"{order.numero_orden}_{_slug(order.customer.nombre_completo)}_{document.file_stem}.pdf"


def document_html(session: Session, order: ServiceOrder, kind: DocumentKind | str) -> str:
    """HTML del documento pedido. Lanza ValueError si el tipo no existe."""
    builders = {
        DocumentKind.RECEPCION: receipt_html,
        DocumentKind.PRESUPUESTO: budget_html,
        DocumentKind.INFORME: technical_report_html,
        DocumentKind.ENTREGA: delivery_html,
        DocumentKind.HISTORIAL: history_html,
    }
    try:
        build = builders[DocumentKind(kind)]
    except ValueError as exc:
        raise ValueError(QCoreApplication.translate("LucioTech", "Unknown document: {kind}").format(kind=repr(kind))) from exc
    return build(session, order)


def receipt_html(session: Session, order: ServiceOrder) -> str:
    """Comprobante de recepción listo para imprimir (§13.1.1)."""
    customer = order.customer
    equipment = order.equipment

    parts = [_header(session, order, DocumentKind.RECEPCION)]
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Customer"),
            [
                (QCoreApplication.translate("LucioTech", "Name"), customer.nombre_completo),
                (QCoreApplication.translate("LucioTech", "ID number"), customer.numero_identificacion or EMPTY),
                (QCoreApplication.translate("LucioTech", "Phone"), customer.telefono_principal or EMPTY),
                (QCoreApplication.translate("LucioTech", "Email"), customer.correo_electronico or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Equipment received"),
            [
                (
                    QCoreApplication.translate("LucioTech", "Type"),
                    equipment_type_label(equipment.tipo_equipo),
                ),
                (QCoreApplication.translate("LucioTech", "Brand and model"), _brand_model(order) or EMPTY),
                (QCoreApplication.translate("LucioTech", "Serial number"), equipment.numero_serie or EMPTY),
                (QCoreApplication.translate("LucioTech", "Colour"), equipment.color or EMPTY),
                (QCoreApplication.translate("LucioTech", "Operating system"), equipment.sistema_operativo or EMPTY),
                (QCoreApplication.translate("LucioTech", "Accessories received"), equipment.accesorios_recibidos or EMPTY),
                (QCoreApplication.translate("LucioTech", "Physical condition"), equipment.estado_fisico or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Reception"),
            [
                (QCoreApplication.translate("LucioTech", "Received on"), format_datetime(order.fecha_ingreso)),
                (QCoreApplication.translate("LucioTech", "Estimated delivery"), format_datetime(order.fecha_estimada_entrega) or EMPTY),
                (QCoreApplication.translate("LucioTech", "Technician in charge"), order.tecnico_responsable or EMPTY),
                (
                    QCoreApplication.translate("LucioTech", "Reported problem"),
                    order.problema_reportado or equipment.problema_reportado_cliente or EMPTY,
                ),
                (QCoreApplication.translate("LucioTech", "Intake notes"), equipment.observaciones_ingreso or EMPTY),
            ],
        )
    )
    parts.append(_values_html(session, order))
    parts.append(_photos_html(order))
    parts.append(_legal_html(session, order))
    parts.append(_signatures(QCoreApplication.translate("LucioTech", "Customer signature"), QCoreApplication.translate("LucioTech", "Workshop signature")))
    parts.append("</div>")
    return "".join(parts)


def budget_html(session: Session, order: ServiceOrder) -> str:
    """Presupuesto con las líneas, los totales, la validez y el espacio de aprobación (§13.1.3)."""
    tax = tax_settings(session)
    totals = order_totals(order, tax)
    days = budget_validity_days(session)

    parts = [_header(session, order, DocumentKind.PRESUPUESTO)]
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Customer"),
            [
                (QCoreApplication.translate("LucioTech", "Name"), order.customer.nombre_completo),
                (QCoreApplication.translate("LucioTech", "ID number"), order.customer.numero_identificacion or EMPTY),
                (QCoreApplication.translate("LucioTech", "Phone"), order.customer.telefono_principal or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Equipment"),
            [
                (
                    QCoreApplication.translate("LucioTech", "Type"),
                    equipment_type_label(order.equipment.tipo_equipo),
                ),
                (QCoreApplication.translate("LucioTech", "Brand and model"), _brand_model(order) or EMPTY),
                (QCoreApplication.translate("LucioTech", "Serial number"), order.equipment.numero_serie or EMPTY),
                (QCoreApplication.translate("LucioTech", "Reported problem"), order.problema_reportado or EMPTY),
            ],
        )
    )

    rows = _concept_rows(order)
    if rows:
        parts.append(
            _table_section(
                QCoreApplication.translate("LucioTech", "Budget details"),
                (QCoreApplication.translate("LucioTech", "Item"), QCoreApplication.translate("LucioTech", "Qty."), QCoreApplication.translate("LucioTech", "Unit price"), QCoreApplication.translate("LucioTech", "Amount")),
                rows,
                widths=("46%", "8%", "23%", "23%"),
                align_right=(1, 2, 3),
            )
        )
    else:
        parts.append(
            f'<p style="margin: 10pt 0 2pt 0;"><b>{QCoreApplication.translate("LucioTech", "Budget details")}</b></p>'
            f'<p style="margin: 0;">{EMPTY}</p>'
        )

    parts.append(_totals_section(totals, order, tax, with_payments=False))
    parts.append(
        '<p style="margin: 12pt 0 0 0;">'
        + QCoreApplication.translate("LucioTech", "Budget valid for {days} days from {date}. Work starts once approved.").format(
            days=days, date=format_datetime(order.fecha_ingreso)
        )
        + "</p>"
    )
    parts.append(_legal_html(session, order))
    parts.append(
        f'<p style="margin: 18pt 0 2pt 0;"><b>{QCoreApplication.translate("LucioTech", "Customer approval")}</b></p>'
        f'<p style="margin: 0;">{QCoreApplication.translate("LucioTech", "Name: {signature}   Date: ______________").format(signature=SIGNATURE)}</p>'
        f'<p style="margin: 14pt 0 0 0;">{QCoreApplication.translate("LucioTech", "Signature: {signature}").format(signature=SIGNATURE)}</p>'
    )
    parts.append("</div>")
    return "".join(parts)


def technical_report_html(session: Session, order: ServiceOrder) -> str:
    """Informe técnico: diagnóstico, trabajo, repuestos, fotos, costos y garantía (§13.1.2)."""
    equipment = order.equipment
    tax = tax_settings(session)
    totals = order_totals(order, tax)

    parts = [_header(session, order, DocumentKind.INFORME)]
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Customer"),
            [
                (QCoreApplication.translate("LucioTech", "Name"), order.customer.nombre_completo),
                (QCoreApplication.translate("LucioTech", "ID number"), order.customer.numero_identificacion or EMPTY),
                (QCoreApplication.translate("LucioTech", "Phone"), order.customer.telefono_principal or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Equipment"),
            [
                (
                    QCoreApplication.translate("LucioTech", "Type"),
                    equipment_type_label(equipment.tipo_equipo),
                ),
                (QCoreApplication.translate("LucioTech", "Brand and model"), _brand_model(order) or EMPTY),
                (QCoreApplication.translate("LucioTech", "Serial number"), equipment.numero_serie or EMPTY),
                (QCoreApplication.translate("LucioTech", "Physical condition on arrival"), equipment.estado_fisico or EMPTY),
                (QCoreApplication.translate("LucioTech", "Accessories received"), equipment.accesorios_recibidos or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Order"),
            [
                (QCoreApplication.translate("LucioTech", "Received on"), format_datetime(order.fecha_ingreso)),
                (QCoreApplication.translate("LucioTech", "Current status"), state_label(order.estado)),
                (QCoreApplication.translate("LucioTech", "Technician in charge"), order.tecnico_responsable or EMPTY),
                (QCoreApplication.translate("LucioTech", "Reported problem"), order.problema_reportado or EMPTY),
            ],
        )
    )
    parts.append(_rich_section(QCoreApplication.translate("LucioTech", "Technical diagnosis"), order.diagnostico_html))
    parts.append(_rich_section(QCoreApplication.translate("LucioTech", "Work performed"), order.trabajo_realizado_html))
    parts.append(_rich_section(QCoreApplication.translate("LucioTech", "Parts used"), _lines(_parts_used(order))))
    parts.append(_rich_section(QCoreApplication.translate("LucioTech", "Recommendations"), order.recomendaciones_html))
    parts.append(
        _photos_html(order, only=_BEFORE, title=QCoreApplication.translate("LucioTech", "Photographs of the equipment on arrival"))
    )
    parts.append(
        _photos_html(order, only=_AFTER, title=QCoreApplication.translate("LucioTech", "Photographs of the repaired equipment"))
    )
    parts.append(_totals_section(totals, order, tax))
    parts.append(_section(QCoreApplication.translate("LucioTech", "Warranty"), [(QCoreApplication.translate("LucioTech", "Warranty"), _warranty(session, order))]))
    parts.append(_legal_html(session, order))
    parts.append(_signatures(QCoreApplication.translate("LucioTech", "Technician signature"), QCoreApplication.translate("LucioTech", "Customer signature")))
    parts.append("</div>")
    return "".join(parts)


def delivery_html(session: Session, order: ServiceOrder) -> str:
    """Comprobante de entrega: trabajo, pagos, saldo, garantía y conformidad (§13.1.4)."""
    tax = tax_settings(session)
    totals = order_totals(order, tax)

    parts = [_header(session, order, DocumentKind.ENTREGA)]
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Order"),
            [
                (QCoreApplication.translate("LucioTech", "Received on"), format_datetime(order.fecha_ingreso)),
                (QCoreApplication.translate("LucioTech", "Delivery date"), format_datetime(order.fecha_entrega) or EMPTY),
                (QCoreApplication.translate("LucioTech", "Final status"), state_label(order.estado)),
                (QCoreApplication.translate("LucioTech", "Technician in charge"), order.tecnico_responsable or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Customer"),
            [
                (QCoreApplication.translate("LucioTech", "Name"), order.customer.nombre_completo),
                (QCoreApplication.translate("LucioTech", "ID number"), order.customer.numero_identificacion or EMPTY),
                (QCoreApplication.translate("LucioTech", "Phone"), order.customer.telefono_principal or EMPTY),
            ],
        )
    )
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Equipment"),
            [
                (
                    QCoreApplication.translate("LucioTech", "Type"),
                    equipment_type_label(order.equipment.tipo_equipo),
                ),
                (QCoreApplication.translate("LucioTech", "Brand and model"), _brand_model(order) or EMPTY),
                (QCoreApplication.translate("LucioTech", "Serial number"), order.equipment.numero_serie or EMPTY),
            ],
        )
    )
    parts.append(_rich_section(QCoreApplication.translate("LucioTech", "Work performed"), order.trabajo_realizado_html))
    parts.append(_payments_section(order))
    parts.append(_totals_section(totals, order, tax))
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Warranty"),
            [
                (QCoreApplication.translate("LucioTech", "Coverage"), _warranty(session, order)),
                (
                    QCoreApplication.translate("LucioTech", "Scope"),
                    QCoreApplication.translate("LucioTech", "Covers only the work performed and the parts invoiced."),
                ),
            ],
        )
    )
    parts.append(_legal_html(session, order))
    parts.append(
        f'<p style="margin: 12pt 0 0 0;"><b>{QCoreApplication.translate("LucioTech", "Declaration of conformity")}</b></p>'
        f'<p style="margin: 0;">{QCoreApplication.translate("LucioTech", "I received the equipment in the condition described, tested and working, and I accept the warranty coverage stated above.")}</p>'
    )
    parts.append(_signatures(QCoreApplication.translate("LucioTech", "Customer signature"), QCoreApplication.translate("LucioTech", "Workshop signature")))
    parts.append("</div>")
    return "".join(parts)


def history_html(session: Session, order: ServiceOrder) -> str:
    """Historial completo: todos los movimientos de la orden en orden cronológico (§13.1.5)."""
    parts = [_header(session, order, DocumentKind.HISTORIAL)]
    parts.append(
        _section(
            QCoreApplication.translate("LucioTech", "Order"),
            [
                (QCoreApplication.translate("LucioTech", "Customer"), order.customer.nombre_completo),
                (
                    QCoreApplication.translate("LucioTech", "Equipment"),
                    f"{equipment_type_label(order.equipment.tipo_equipo)} "
                    f"{_brand_model(order)}".strip(),
                ),
                (QCoreApplication.translate("LucioTech", "Received on"), format_datetime(order.fecha_ingreso)),
                (QCoreApplication.translate("LucioTech", "Current status"), state_label(order.estado)),
            ],
        )
    )
    rows = [
        (
            format_datetime(entry.fecha),
            QCoreApplication.translate("LucioTech", "Status") if entry.kind == "estado" else QCoreApplication.translate("LucioTech", "Event"),
            f"{event_title_label(entry.titulo)}. {history_detail_label(entry.detalle)}".strip(),
            entry.usuario,
        )
        for entry in order_timeline(order)
    ]
    if rows:
        parts.append(
            _table_section(
                QCoreApplication.translate("LucioTech", "Movements"),
                (QCoreApplication.translate("LucioTech", "Date"), QCoreApplication.translate("LucioTech", "Type"), QCoreApplication.translate("LucioTech", "Detail"), QCoreApplication.translate("LucioTech", "User")),
                rows,
                widths=("16%", "10%", "56%", "18%"),
            )
        )
    else:
        parts.append(
            f'<p style="margin: 10pt 0 2pt 0;"><b>{QCoreApplication.translate("LucioTech", "Movements")}</b></p>'
            f'<p style="margin: 0;">{EMPTY}</p>'
        )
    parts.append("</div>")
    return "".join(parts)


def print_document(
    html: str,
    parent: QWidget | None,
    title: str,
    furniture: PageFurniture | None = None,
    pdf_name: str | None = None,
    paper: str = DEFAULT_PAPER_SIZE,
    margin_mm: int = DEFAULT_PAGE_MARGIN_MM,
) -> None:
    """Vista previa, impresión y guardado en PDF del documento (§13.2 y §13.3).

    El propio diálogo de Qt aporta impresora, orientación, tamaño de hoja, márgenes, rango de
    páginas y copias. Encima se añade el encabezado y el pie con la numeración, y un botón
    «Guardar como PDF» que propone el nombre descriptivo de la orden.
    """
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    apply_page_setup(printer, paper, margin_mm)
    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle(title)
    size_preview(preview, parent)
    preview.paintRequested.connect(lambda target: render_document(target, html, furniture))
    add_pdf_action(preview, printer, html, furniture, pdf_name or f"{title}.pdf")
    preview.exec()


def print_order_document(
    session_factory: sessionmaker[Session],
    order_id: int,
    kind: DocumentKind | str,
    parent: QWidget | None = None,
    title: str | None = None,
    printed_by: str | None = None,
) -> bool:
    """Abre la vista previa del documento pedido.

    `printed_by` es el nombre del usuario que tiene la sesión abierta: va en el pie de cada
    hoja, para que el papel diga quién lo imprimió. Devuelve True si el documento se pudo
    preparar; si la orden ya no existe o falla la consulta, avisa al usuario y devuelve False.
    """
    document = DocumentKind(kind)
    window_title = title or document_label(document)
    try:
        with session_factory() as session:
            order = session.get(ServiceOrder, order_id)
            if order is None:
                QMessageBox.warning(
                    parent,
                    window_title,
                    QCoreApplication.translate("LucioTech", "The order no longer exists."),
                )
                return False
            html = document_html(session, order, document)
            furniture = _furniture(session, order, document, printed_by)
            pdf_name = pdf_filename(order, document)
            paper = paper_size(session)
            margin = page_margin_mm(session)
    except SQLAlchemyError:
        QMessageBox.critical(
            parent,
            window_title,
            QCoreApplication.translate(
                _CONTEXT, "The document could not be prepared. Please try again."
            ),
        )
        return False
    print_document(
        html,
        parent,
        window_title,
        furniture=furniture,
        pdf_name=pdf_name,
        paper=paper,
        margin_mm=margin,
    )
    return True


def print_order_receipt(
    session_factory: sessionmaker[Session],
    order_id: int,
    parent: QWidget | None = None,
    title: str | None = None,
    printed_by: str | None = None,
) -> bool:
    """Atajo del comprobante de recepción, que es el documento de la lista de órdenes."""
    return print_order_document(
        session_factory, order_id, DocumentKind.RECEPCION, parent, title, printed_by
    )


def _furniture(
    session: Session,
    order: ServiceOrder,
    kind: DocumentKind | str,
    printed_by: str | None = None,
) -> PageFurniture:
    """Encabezado y pie que se repiten en cada hoja (§13.2).

    El encabezado lleva el taller y el documento con su número de orden; el pie, la fecha de
    generación y quién lo imprime. La numeración la pone `render_document`, que es quien cuenta
    las hojas.
    """
    name = workshop_name(session)
    contact = workshop_contact(session)
    footer = QCoreApplication.translate("LucioTech", "Generated on {date}").format(date=format_datetime(datetime.now()))
    if printed_by:
        footer = QCoreApplication.translate("LucioTech", "{footer} by {user}").format(footer=footer, user=printed_by)
    return PageFurniture(
        header_left=f"{name} · {contact}" if contact else name,
        header_right=f"{document_label(kind)} · {order.numero_orden}",
        footer_left=footer,
    )


def _header(session: Session, order: ServiceOrder, title: DocumentKind | str) -> str:
    parts = [
        '<div style="font-size: 10pt;">',
        '<p style="font-size: 15pt; font-weight: bold; margin: 0;">'
        f"{_escape(workshop_name(session))}</p>",
    ]
    contact = workshop_contact(session)
    if contact:
        parts.append(f'<p style="margin: 0;">{_escape(contact)}</p>')
    parts.append(
        '<p style="margin: 10pt 0 4pt 0; font-size: 12pt;">'
        f"<b>{_escape(str(title))}</b> &nbsp;&nbsp; {_escape(order.numero_orden)}</p>"
    )
    return "".join(parts)


def _values_html(session: Session, order: ServiceOrder) -> str:
    """Sección «Valores» del comprobante.

    Se arma con `order_totals`, la misma fórmula que usa la pestaña «Presupuesto y pagos»
    (§5.3), para que el papel y la pantalla nunca muestren cifras distintas. Las filas que
    pueden ser cero (repuestos, mano de obra, líneas, descuento, pagos) solo aparecen cuando
    tienen importe; el total y el saldo salen siempre. El IVA solo se imprime si está activo:
    al cliente no se le muestra una línea de impuesto en cero.
    """
    tax = tax_settings(session)
    totals = order_totals(order, tax)
    rows: list[tuple[str, str]] = [
        (QCoreApplication.translate("LucioTech", "Diagnosis cost"), format_money(order.costo_diagnostico)),
    ]
    if _positive(totals.lineas_presupuesto):
        rows.append((QCoreApplication.translate("LucioTech", "Budget lines"), format_money(totals.lineas_presupuesto)))
    rows.append((QCoreApplication.translate("LucioTech", "Subtotal"), format_money(totals.subtotal)))
    if _positive(order.descuento):
        rows.append((QCoreApplication.translate("LucioTech", "Discount"), format_money(order.descuento)))
    if tax.enabled:
        rows.append((QCoreApplication.translate("LucioTech", "Tax ({percent}%)").format(percent=tax.percent), format_money(totals.impuestos)))
    rows.append((QCoreApplication.translate("LucioTech", "Total"), format_money(totals.total)))
    rows.append((QCoreApplication.translate("LucioTech", "Deposit received"), format_money(order.anticipo)))
    if totals.pagos_realizados != ZERO:
        rows.append((QCoreApplication.translate("LucioTech", "Payments received"), format_money(totals.pagos_realizados)))
    rows.append((QCoreApplication.translate("LucioTech", "Outstanding balance"), format_money(totals.saldo_pendiente)))
    return _section(
        QCoreApplication.translate("LucioTech", "Values"),
        rows,
        bold=(
            QCoreApplication.translate("LucioTech", "Total"),
            QCoreApplication.translate("LucioTech", "Outstanding balance"),
        ),
    )


def _totals_section(
    totals: OrderTotals, order: ServiceOrder, tax, with_payments: bool = True
) -> str:
    """Bloque de importes compartido por el presupuesto, el informe y la entrega.

    El presupuesto no imprime anticipos ni pagos: es una oferta, no un estado de cuenta.
    """
    rows = [(QCoreApplication.translate("LucioTech", "Subtotal"), format_money(totals.subtotal))]
    if _positive(order.descuento):
        rows.append((QCoreApplication.translate("LucioTech", "Discount"), format_money(order.descuento)))
    if tax.enabled:
        rows.append((QCoreApplication.translate("LucioTech", "Tax ({percent}%)").format(percent=tax.percent), format_money(totals.impuestos)))
    rows.append((QCoreApplication.translate("LucioTech", "Total"), format_money(totals.total)))
    if with_payments:
        if _positive(order.anticipo):
            rows.append((QCoreApplication.translate("LucioTech", "Deposit received"), format_money(order.anticipo)))
        if totals.pagos_realizados != ZERO:
            rows.append((QCoreApplication.translate("LucioTech", "Payments received"), format_money(totals.pagos_realizados)))
        rows.append((QCoreApplication.translate("LucioTech", "Outstanding balance"), format_money(totals.saldo_pendiente)))
        return _section(
            QCoreApplication.translate("LucioTech", "Amounts"), rows, bold=(QCoreApplication.translate("LucioTech", "Total"), QCoreApplication.translate("LucioTech", "Outstanding balance"))
        )
    return _section(QCoreApplication.translate("LucioTech", "Amounts"), rows, bold=(QCoreApplication.translate("LucioTech", "Total"),))


def _concept_rows(order: ServiceOrder) -> list[tuple[str, str, str, str]]:
    """Conceptos del presupuesto: el costo de diagnóstico (si tiene importe) y las líneas."""
    rows: list[tuple[str, str, str, str]] = []
    fixed = ((QCoreApplication.translate("LucioTech", "Diagnosis cost"), order.costo_diagnostico),)
    for label, amount in fixed:
        if _positive(amount):
            rows.append((label, "1", format_money(amount), format_money(amount)))
    for line in order.budget_lines:
        amount = line.cantidad * line.precio_unitario
        rows.append(
            (
                f"{budget_line_type_label(line.tipo_linea)}: {line.descripcion}",
                _quantity(line.cantidad),
                format_money(line.precio_unitario),
                format_money(amount),
            )
        )
    return rows


def _payments_section(order: ServiceOrder) -> str:
    rows = [
        (
            format_datetime(payment.fecha),
            payment_type_label(payment.tipo_pago),
            payment_method_label(payment.metodo_pago),
            format_money(payment.monto),
            QCoreApplication.translate("LucioTech", "Voided") if payment.anulado else QCoreApplication.translate("LucioTech", "Current"),
        )
        for payment in payments_for_order(order)
    ]
    if not rows:
        return _section(QCoreApplication.translate("LucioTech", "Payments"), [(QCoreApplication.translate("LucioTech", "Payments received"), EMPTY)])
    return _table_section(
        QCoreApplication.translate("LucioTech", "Payments"),
        (QCoreApplication.translate("LucioTech", "Date"), QCoreApplication.translate("LucioTech", "Type"), QCoreApplication.translate("LucioTech", "Method"), QCoreApplication.translate("LucioTech", "Amount"), QCoreApplication.translate("LucioTech", "Status")),
        rows,
        widths=("18%", "18%", "30%", "20%", "14%"),
        align_right=(3,),
    )


def _parts_used(order: ServiceOrder) -> str:
    """Repuestos: el texto libre si existe; si no, las líneas de tipo Repuesto."""
    if (order.repuestos_utilizados or "").strip():
        return order.repuestos_utilizados.strip()
    parts = [
        f"{_quantity(line.cantidad)} × {line.descripcion}"
        for line in order.budget_lines
        if line.tipo_linea == BudgetLineType.REPUESTO.value
    ]
    return ", ".join(parts) or EMPTY


def _warranty(session: Session, order: ServiceOrder) -> str:
    days = effective_warranty_days(session, order)
    if days <= 0:
        return QCoreApplication.translate("LucioTech", "No warranty recorded")
    return QCoreApplication.translate("LucioTech", "{days} days").format(days=days)


def _brand_model(order: ServiceOrder) -> str:
    return " ".join(part for part in (order.equipment.marca, order.equipment.modelo) if part)


def _positive(value: Decimal | None) -> bool:
    return value is not None and value > ZERO


def _quantity(value: Decimal) -> str:
    """Cantidad sin ceros de relleno y sin notación científica: 2.00 → «2»."""
    return format(value.normalize(), "f")


def _section(
    title: str,
    rows: list[tuple[str, str]],
    bold: tuple[str, ...] = (),
) -> str:
    body = "".join(
        f'<tr><td style="{_CELL}"><b>{_escape(label)}</b></td>'
        f'<td style="{_CELL}">{_cell(label, value, bold)}</td></tr>'
        for label, value in rows
    )
    return (
        f'<p style="margin: 6pt 0 1pt 0;"><b>{_escape(title)}</b></p>'
        f'<table width="100%" cellspacing="0" cellpadding="0">{body}</table>'
    )


def _rich_section(title: str, html: str | None) -> str:
    """Bloque de texto enriquecido: diagnóstico, trabajo realizado o recomendaciones."""
    body = (html or "").strip()
    return (
        f'<p style="margin: 6pt 0 1pt 0;"><b>{_escape(title)}</b></p>'
        f'<p style="margin: 0;">{body or EMPTY}</p>'
    )


def _table_section(
    title: str,
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    widths: tuple[str, ...] | None = None,
    align_right: tuple[int, ...] = (),
) -> str:
    """Tabla con encabezado y borde inferior, para líneas, pagos e historial."""
    spans = widths or tuple("" for _ in headers)

    def cell(text: str, index: int, style: str) -> str:
        align = _RIGHT if index in align_right else ""
        width = f' width="{spans[index]}"' if spans[index] else ""
        return f'<td{width} style="{style}{align}">{_escape(text)}</td>'

    head = "".join(cell(header, index, _HEAD_CELL) for index, header in enumerate(headers))
    body = "".join(
        "<tr>"
        + "".join(cell(value, index, _CELL) for index, value in enumerate(row))
        + "</tr>"
        for row in rows
    )
    return (
        f'<p style="margin: 6pt 0 1pt 0;"><b>{_escape(title)}</b></p>'
        f'<table width="100%" cellspacing="0" cellpadding="0"><tr>{head}</tr>{body}</table>'
    )


def _cell(label: str, value: str, bold: tuple[str, ...]) -> str:
    escaped = _escape(value)
    return f"<b>{escaped}</b>" if label in bold else escaped


def _photos_html(
    order: ServiceOrder,
    only: tuple[PhotoType, ...] | None = None,
    title: str | None = None,
) -> str:
    photos = _photos(order, only)
    if not photos:
        return ""
    title = title or QCoreApplication.translate("LucioTech", "Photographs of the equipment")
    cells = "".join(
        f'<td style="padding: 0 6pt 0 0;">'
        f'<img src="{_escape(_file_uri(photo.ruta_archivo))}" width="110"></td>'
        for photo in photos
    )
    return (
        f'<p style="margin: 6pt 0 1pt 0;"><b>{_escape(title)}</b></p>'
        f'<table cellspacing="0" cellpadding="0"><tr>{cells}</tr></table>'
    )


def _photos(
    order: ServiceOrder, only: tuple[PhotoType, ...] | None = None
) -> list[Photograph]:
    photos = list(order.photographs)
    if only is not None:
        wanted = {kind.value for kind in only}
        photos = [photo for photo in photos if photo.tipo_fotografia in wanted]
    return photos[:MAX_PHOTOS]


def _signatures(*labels: str) -> str:
    cells = "".join(
        f'<td style="padding-right: 20pt;">{SIGNATURE}<br/>{_escape(label)}</td>'
        for label in labels
    )
    return (
        '<table width="100%" cellspacing="0" cellpadding="0" style="margin-top: 18pt;">'
        f"<tr>{cells}</tr></table>"
    )


def _file_uri(path: str) -> str:
    try:
        return Path(path).resolve().as_uri()
    except (OSError, ValueError):
        return path


def _slug(text: str) -> str:
    """Nombre del cliente apto para un archivo: «Ana Torres» → «Ana-Torres»."""
    plain = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in plain if not unicodedata.combining(char))
    return re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-") or "Cliente"


def _text_block(title: str, text: str) -> str:
    """Apartado de texto legal: título en negrita y cada línea del usuario en su propia línea."""
    return (
        f'<p style="margin: 10pt 0 2pt 0;"><b>{_escape(title)}</b></p>'
        f'<p style="margin: 0;">{_lines(text)}</p>'
    )


def _legal_html(session: Session, order: ServiceOrder) -> str:
    """Términos y condiciones y garantía, iguales en todo documento entregado al cliente.

    El historial completo es interno y no los lleva. Si el taller tiene la garantía en cero
    días, o el texto se dejó en blanco en Configuración, el apartado de garantía no se imprime.
    """
    parts: list[str] = []
    terms = service_conditions(session)
    if terms:
        parts.append(_text_block(QCoreApplication.translate("LucioTech", "Terms and conditions"), terms))
    warranty = warranty_conditions(session, order)
    if warranty:
        parts.append(_text_block(QCoreApplication.translate("LucioTech", "Warranty conditions"), warranty))
    return "".join(parts)


def _lines(text: str) -> str:
    return _escape(text).replace("\n", "<br/>")


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _catalog() -> None:
    """Mantiene los textos en el catálogo de pylupdate6; no se ejecuta nunca."""
    QCoreApplication.translate("LucioTech", "Reception receipt")
    QCoreApplication.translate("LucioTech", "Budget")
    QCoreApplication.translate("LucioTech", "Technical report")
    QCoreApplication.translate("LucioTech", "Delivery receipt")
    QCoreApplication.translate("LucioTech", "Full history")
