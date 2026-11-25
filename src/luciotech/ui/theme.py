"""Temas de la aplicación: sistema, claro y oscuro.

En Linux el tema del sistema puede ser el configurado con Qt6Ct/Kvantum; en Windows y
macOS es el nativo de cada plataforma. Los temas claro y oscuro se aplican con el estilo
Fusion y una paleta propia, de forma que funcionen en cualquier sistema operativo.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QStyleFactory


_SYSTEM_STYLE: str | None = None
_SYSTEM_PALETTE: QPalette | None = None


def init_theme_state(app: QApplication) -> None:
    """Guarda el estilo y la paleta originales para poder volver al tema del sistema."""
    global _SYSTEM_STYLE, _SYSTEM_PALETTE
    _SYSTEM_STYLE = app.style().objectName()
    _SYSTEM_PALETTE = app.palette()


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    return palette


def apply_theme(mode: str) -> None:
    """Aplica el tema indicado (``system``, ``light`` o ``dark``) a la aplicación."""
    app = QApplication.instance()
    if app is None:
        return
    if mode == "dark":
        app.setStyle("Fusion")
        app.setPalette(_dark_palette())
    elif mode == "light":
        app.setStyle("Fusion")
        app.setPalette(QPalette())
    else:  # system
        if _SYSTEM_STYLE:
            app.setStyle(_SYSTEM_STYLE)
        if _SYSTEM_PALETTE is not None:
            app.setPalette(_SYSTEM_PALETTE)