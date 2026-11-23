"""Textos predefinidos para diagnóstico, trabajo y recomendaciones (§8 del ROADMAP).

Se guardan en la tabla configuracion, una frase por línea. Si nunca se han configurado,
se usan los valores por defecto de config.py.
"""

from __future__ import annotations

from PyQt6.QtCore import QCoreApplication
from sqlalchemy.orm import Session

from luciotech.config import DEFAULT_PREDEFINED_TEXTS
from luciotech.services.settings_service import get_value, set_value

KEY_PREDEFINED_TEXTS = "textos_predefinidos"


def default_predefined_texts() -> list[str]:
    """Frases por defecto en el idioma elegido (el inglés es el texto fuente)."""
    return [
        QCoreApplication.translate("LucioTech", text) for text in DEFAULT_PREDEFINED_TEXTS
    ]


def predefined_texts(session: Session) -> list[str]:
    raw = get_value(session, KEY_PREDEFINED_TEXTS)
    if raw is None:
        return default_predefined_texts()
    items = [line.strip() for line in raw.splitlines() if line.strip()]
    return items or default_predefined_texts()


def save_predefined_texts(session: Session, texts: list[str]) -> None:
    """Reemplaza la lista completa. Descarta líneas vacías y no permite saltos de línea dentro de una frase."""
    cleaned = [" ".join(text.split()) for text in texts]
    cleaned = [text for text in cleaned if text]
    if not cleaned:
        raise ValueError(
            QCoreApplication.translate(
                "LucioTech", "The list of predefined texts cannot be empty."
            )
        )
    set_value(session, KEY_PREDEFINED_TEXTS, "\n".join(cleaned))


def _catalog() -> None:
    """Mantiene las frases por defecto en el catálogo de pylupdate6; no se ejecuta nunca."""
    QCoreApplication.translate("LucioTech", "A visual inspection of the equipment was performed.")
    QCoreApplication.translate("LucioTech", "Power-on tests were performed.")
    QCoreApplication.translate("LucioTech", "The storage condition was checked.")
    QCoreApplication.translate("LucioTech", "The RAM was checked.")
    QCoreApplication.translate("LucioTech", "Preventive maintenance is recommended.")
    QCoreApplication.translate("LucioTech", "Replacing the faulty component is recommended.")
    QCoreApplication.translate("LucioTech", "The equipment was tested and works correctly.")
