"""Accesorios sugeridos según el tipo de equipo (§7.2 del ROADMAP)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

OTHER = "Otro"

CAMERA_ACCESSORIES: tuple[str, ...] = (
    "Fuente de alimentación",
    "Adaptador",
    "Cable",
    "Disco duro",
    "Control remoto",
    "Mouse",
    "Antena",
    OTHER,
)

ACCESSORIES_BY_TYPE: dict[str, tuple[str, ...]] = {
    "Laptop": ("Cargador", "Batería", "Bolso", "Mouse", "Adaptador", "Memoria USB", OTHER),
    "Computadora de escritorio": (
        "Cable de corriente",
        "Monitor",
        "Teclado",
        "Mouse",
        "Parlantes",
        "Adaptador Wi-Fi",
        OTHER,
    ),
    "Impresora": ("Cable de corriente", "Cable USB", "Cartuchos", "Botellas de tinta", "Bandejas", OTHER),
    "Cámara de seguridad": CAMERA_ACCESSORIES,
    "DVR": CAMERA_ACCESSORIES,
    "NVR": CAMERA_ACCESSORIES,
}


def suggested_accessories(tipo_equipo: str) -> tuple[str, ...]:
    return ACCESSORIES_BY_TYPE.get(tipo_equipo, (OTHER,))


def build_accessories_text(
    selected: Iterable[str],
    manual: str | None,
    details: Mapping[str, str] | None = None,
) -> str | None:
    """Une los accesorios marcados (con su detalle, p. ej. 'Batería (Dell XPS 13)') y el texto libre.

    Devuelve None si no hay ningún accesorio ni texto libre.
    """
    details = details or {}
    items: list[str] = []
    for name in selected:
        cleaned = name.strip()
        if not cleaned:
            continue
        detail = (details.get(cleaned) or "").strip()
        items.append(f"{cleaned} ({detail})" if detail else cleaned)
    extra = (manual or "").strip()
    if extra:
        items.append(extra)
    return ", ".join(items) or None
