"""Textos visibles para errores de validación y nombres de campos."""

from __future__ import annotations

from PyQt6.QtCore import QCoreApplication

_CONTEXT = "LucioTech"

_ERROR_TEXTS = {
    "required": "This field is required.",
    "cedula.length": "The ID number must have 10 digits.",
    "cedula.not_digits": "The ID number may only contain digits.",
    "cedula.province": "Invalid province code (01 to 24, or 30).",
    "cedula.third_digit": "The third digit must be between 0 and 5 for private individuals.",
    "cedula.check_digit": "The ID number is not valid (check digit).",
    "phone.invalid_chars": "The phone may only contain digits, spaces, +, - and brackets.",
    "phone.length": "The phone must have between 7 and 15 digits.",
    "email.invalid": "Invalid email address.",
    "invalid_type": "Select an equipment type from the list.",
    "not_found": "The selected customer no longer exists.",
    "customer.required": "Select an existing customer or fill in the new customer details.",
    "amount.negative": "The amount cannot be negative.",
    "amount.invalid": "Invalid amount. Use digits and a decimal point only.",
    "anticipo.exceeds_total": "The deposit cannot exceed the total including taxes.",
    "date.before_entry": "The estimated date cannot be earlier than the received date.",
    "amount.must_be_positive": "The amount must be greater than zero.",
    "refund.exceeds_paid": "You cannot refund more than has been paid.",
    "deposit.already_registered": (
        "A deposit was already recorded at reception; this payment will be subtracted on top "
        "of that deposit."
    ),
    "payment.already_voided": "This payment was already voided.",
    "equipment.other_customer": "The selected equipment does not belong to this customer.",
}

_FIELD_LABELS = {
    "nombre_completo": "Full name",
    "numero_identificacion": "ID, tax ID or identification",
    "telefono_principal": "Primary phone",
    "telefono_secundario": "Secondary phone",
    "correo_electronico": "Email",
    "cliente_id": "Customer",
    "tipo_equipo": "Equipment type",
    "cliente": "Customer",
    "costo_diagnostico": "Diagnosis cost",
    "anticipo": "Deposit received",
    "descuento": "Discount",
    "cantidad": "Quantity",
    "precio_unitario": "Unit price",
    "descripcion": "Description",
    "tipo_linea": "Type",
    "fecha_estimada_entrega": "Estimated delivery date",
    "equipo": "Equipment",
}


def error_text(code: str) -> str:
    source = _ERROR_TEXTS.get(code)
    if source is None:
        return code
    return QCoreApplication.translate("LucioTech", source)


def field_label(field: str) -> str:
    source = _FIELD_LABELS.get(field)
    if source is None:
        return field
    return QCoreApplication.translate("LucioTech", source)


def _catalog() -> None:
    """Mantiene los textos en el catálogo de pylupdate6; no se ejecuta nunca."""
    QCoreApplication.translate("LucioTech", 'This field is required.')
    QCoreApplication.translate("LucioTech", 'The ID number must have 10 digits.')
    QCoreApplication.translate("LucioTech", 'The ID number may only contain digits.')
    QCoreApplication.translate("LucioTech", 'Invalid province code (01 to 24, or 30).')
    QCoreApplication.translate("LucioTech", 'The third digit must be between 0 and 5 for private individuals.')
    QCoreApplication.translate("LucioTech", 'The ID number is not valid (check digit).')
    QCoreApplication.translate("LucioTech", 'The phone may only contain digits, spaces, +, - and brackets.')
    QCoreApplication.translate("LucioTech", 'The phone must have between 7 and 15 digits.')
    QCoreApplication.translate("LucioTech", 'Invalid email address.')
    QCoreApplication.translate("LucioTech", 'Select an equipment type from the list.')
    QCoreApplication.translate("LucioTech", 'The selected customer no longer exists.')
    QCoreApplication.translate("LucioTech", 'Select an existing customer or fill in the new customer details.')
    QCoreApplication.translate("LucioTech", 'The amount cannot be negative.')
    QCoreApplication.translate("LucioTech", 'Invalid amount. Use digits and a decimal point only.')
    QCoreApplication.translate("LucioTech", 'The deposit cannot exceed the total including taxes.')
    QCoreApplication.translate("LucioTech", 'The estimated date cannot be earlier than the received date.')
    QCoreApplication.translate("LucioTech", 'The amount must be greater than zero.')
    QCoreApplication.translate("LucioTech", 'You cannot refund more than has been paid.')
    QCoreApplication.translate("LucioTech", 'A deposit was already recorded at reception; this payment will be subtracted on top of that deposit.')
    QCoreApplication.translate("LucioTech", 'This payment was already voided.')
    QCoreApplication.translate("LucioTech", 'The selected equipment does not belong to this customer.')
    QCoreApplication.translate("LucioTech", 'Full name')
    QCoreApplication.translate("LucioTech", 'ID, tax ID or identification')
    QCoreApplication.translate("LucioTech", 'Primary phone')
    QCoreApplication.translate("LucioTech", 'Secondary phone')
    QCoreApplication.translate("LucioTech", 'Email')
    QCoreApplication.translate("LucioTech", 'Customer')
    QCoreApplication.translate("LucioTech", 'Equipment type')
    QCoreApplication.translate("LucioTech", 'Diagnosis cost')
    QCoreApplication.translate("LucioTech", 'Deposit received')
    QCoreApplication.translate("LucioTech", 'Discount')
    QCoreApplication.translate("LucioTech", 'Quantity')
    QCoreApplication.translate("LucioTech", 'Unit price')
    QCoreApplication.translate("LucioTech", 'Description')
    QCoreApplication.translate("LucioTech", 'Type')
    QCoreApplication.translate("LucioTech", 'Estimated delivery date')
    QCoreApplication.translate("LucioTech", 'Equipment')
