"""Pruebas del validador de cédula ecuatoriana (módulo 10)."""

from __future__ import annotations

import pytest

from luciotech.utils.validators import CedulaError, cedula_error, is_valid_cedula


@pytest.mark.parametrize(
    "value",
    [
        "1710034065",
        "0926687856",
        "3012345678",
        " 1710034065 ",
    ],
)
def test_valid_cedulas_are_accepted(value: str) -> None:
    assert is_valid_cedula(value)
    assert cedula_error(value) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", CedulaError.LENGTH),
        ("171003406", CedulaError.LENGTH),
        ("17100340655", CedulaError.LENGTH),
        ("17100a4065", CedulaError.NOT_DIGITS),
        ("０１７１００３４０６", CedulaError.NOT_DIGITS),
        ("0012345678", CedulaError.PROVINCE),
        ("2512345678", CedulaError.PROVINCE),
        ("3112345678", CedulaError.PROVINCE),
        ("1763456789", CedulaError.THIRD_DIGIT),
        ("1710034066", CedulaError.CHECK_DIGIT),
    ],
)
def test_invalid_cedulas_report_reason(value: str, expected: CedulaError) -> None:
    assert not is_valid_cedula(value)
    assert cedula_error(value) == expected
