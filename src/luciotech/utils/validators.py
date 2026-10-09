"""Validadores de datos de entrada (§7.1.1 del ROADMAP)."""

from __future__ import annotations

from enum import StrEnum

CEDULA_LENGTH = 10
CEDULA_COEFFICIENTS = (2, 1, 2, 1, 2, 1, 2, 1, 2)
CEDULA_VALID_PROVINCES = frozenset(range(1, 25)) | {30}
CEDULA_MAX_NATURAL_PERSON_THIRD_DIGIT = 5


class CedulaError(StrEnum):
    LENGTH = "length"
    NOT_DIGITS = "not_digits"
    PROVINCE = "province"
    THIRD_DIGIT = "third_digit"
    CHECK_DIGIT = "check_digit"


def cedula_error(value: str) -> CedulaError | None:
    """Devuelve el motivo por el que la cédula no es válida, o None si lo es.

    Aplica el módulo 10 sobre los 9 primeros dígitos. No aplica módulo 11,
    que corresponde a la clave de acceso de facturas electrónicas.
    """
    text = value.strip()
    if len(text) != CEDULA_LENGTH:
        return CedulaError.LENGTH
    if not (text.isascii() and text.isdigit()):
        return CedulaError.NOT_DIGITS
    if int(text[:2]) not in CEDULA_VALID_PROVINCES:
        return CedulaError.PROVINCE
    if int(text[2]) > CEDULA_MAX_NATURAL_PERSON_THIRD_DIGIT:
        return CedulaError.THIRD_DIGIT
    if _modulo10_check_digit(text[:9]) != int(text[9]):
        return CedulaError.CHECK_DIGIT
    return None


def is_valid_cedula(value: str) -> bool:
    return cedula_error(value) is None


def _modulo10_check_digit(digits: str) -> int:
    total = 0
    for digit, coefficient in zip(digits, CEDULA_COEFFICIENTS):
        product = int(digit) * coefficient
        if product >= 10:
            product -= 9
        total += product
    return (10 - total % 10) % 10
