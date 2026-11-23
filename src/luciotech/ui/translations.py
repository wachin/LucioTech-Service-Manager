"""Idioma de la aplicación: traducciones propias y de los diálogos de Qt (§21).

El idioma fuente del programa es el inglés. Cada traducción se entrega como un archivo
`luciotech_<código>.qm` compilado desde su `.ts` con `lrelease`; los `.ts` se editan y se
revisan en Qt Linguist. Además se cargan las traducciones de Qt (`qtbase_<código>`,
`qt_<código>`) para que la vista previa de impresión, los botones de los avisos y los
diálogos de archivo hablen el mismo idioma.

El idioma elegido se guarda en la tabla `configuracion` y se aplica al arrancar.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QLibraryInfo, QTranslator
from PyQt6.QtWidgets import QApplication

from luciotech.config import DEFAULT_LANGUAGE

# Nombre de cada idioma escrito en ese mismo idioma: así la lista de Configuración se lee
# igual en cualquier versión de la aplicación.
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français",
    "it": "Italiano",
    "pt": "Português",
    "pt_BR": "Português (Brasil)",
}

TRANSLATIONS_DIR = Path(__file__).resolve().parent / "translations"


def normalize_language(code: str | None) -> str:
    """Convierte «es_ES» o «es-ES» en el código que usan los archivos `.qm`."""
    value = (code or "").strip().replace("-", "_")
    return value or DEFAULT_LANGUAGE


def available_languages() -> dict[str, str]:
    """Idiomas que se pueden elegir: el inglés fuente más cada `.qm` instalado."""
    languages = dict(LANGUAGE_NAMES)
    if TRANSLATIONS_DIR.is_dir():
        for path in sorted(TRANSLATIONS_DIR.glob("luciotech_*.qm")):
            code = path.stem[len("luciotech_") :]
            languages.setdefault(code, code)
    return languages


def install_translations(app: QApplication, language: str | None = None) -> list[QTranslator]:
    """Instala las traducciones del programa y de Qt; devuelve las que se cargaron.

    La lista se devuelve para poder retirarlas (lo hacen las pruebas); en la aplicación se
    quedan puestas toda la sesión. Si un archivo no existe, se sigue con el texto fuente en
    inglés sin romper el arranque.
    """
    code = normalize_language(language)
    installed: list[QTranslator] = []

    program = QTranslator(app)
    if program.load(f"luciotech_{code}", str(TRANSLATIONS_DIR)):
        app.installTranslator(program)
        installed.append(program)

    folder = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    for name in (f"qtbase_{code}", f"qt_{code}"):
        translator = QTranslator(app)
        if translator.load(name, folder):
            app.installTranslator(translator)
            installed.append(translator)
    return installed


def install_spanish_translations(app: QApplication) -> list[QTranslator]:
    """Atajo histórico: carga el español, que es el idioma por defecto del taller."""
    return install_translations(app, "es")
