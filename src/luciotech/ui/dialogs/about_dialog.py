"""Diálogo «Ayuda ▸ Acerca de…» con los créditos del programa.

Las tarjetas de los desarrolladores son las mismas del programa Lucio IVA Calculator:
foto, nombre, correo y Facebook. El bloque de detalles habla de LucioTech Service Manager.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from luciotech.config import APP_CONFIG

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"
ICON_PATH = RESOURCES_DIR / "icons" / "app-icon.svg"
PHOTOS_DIR = RESOURCES_DIR / "photos"

# (nombre, correo, Facebook, archivo de la foto)
DEVELOPERS: tuple[tuple[str, str, str, str], ...] = (
    (
        "Washington Indacochea Delgado",
        "linuxfrontier@proton.me",
        "https://www.facebook.com/wachin.id",
        "Washington_Indacochea_FB_IMG.jpg",
    ),
    (
        "Joseph Lucio Guerrero",
        "josephsteveng@gmail.com",
        "https://www.facebook.com/jose.guerrero.718689",
        "Joseph_Lucio_FB_IMG.jpg",
    ),
)

REPOSITORY_URL = "https://github.com/wachin/LucioTech-Service-Manager"

ABOUT_STYLE = """
#aboutIcon {
    background: #f7f7f7;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 12px;
}
#aboutAppTitle {
    font-size: 19px;
    font-weight: 700;
}
#developerCard {
    background: #fbfbfb;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
}
#developerPhoto {
    border: 2px solid #d0d0d0;
    border-radius: 12px;
}
#aboutText {
    font-size: 14px;
}
"""


class AboutDialog(QDialog):
    """Créditos del programa: los dos desarrolladores y los datos del proyecto."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(self.tr("About…"))
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setMinimumSize(780, 520)
        self.setStyleSheet(ABOUT_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(18)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addStretch(1)
        icon_label = QLabel()
        icon_label.setObjectName("aboutIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setMinimumWidth(168)
        icon_label.setPixmap(QIcon(str(ICON_PATH)).pixmap(QSize(152, 152)))
        title = QLabel(APP_CONFIG.app_name)
        title.setObjectName("aboutAppTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        left.addWidget(icon_label)
        left.addWidget(title)
        left.addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(8)
        developers_title = QLabel(self.tr("Developers"))
        developers_title.setObjectName("dialogTitle")
        developers_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        right.addWidget(developers_title)
        for name, email, facebook, photo in DEVELOPERS:
            right.addWidget(
                self.developer_card(name, email, facebook, PHOTOS_DIR / photo)
            )

        details = QLabel()
        details.setObjectName("aboutText")
        details.setTextFormat(Qt.TextFormat.RichText)
        details.setOpenExternalLinks(True)
        details.setWordWrap(True)
        details.setText(
            self.styled_links(
                self.tr(
                    "<p><b>License</b><br>GNU GPL v3</p>"
                    "<p><b>Technologies used</b><br>Python, PyQt6, SQLAlchemy, Alembic, "
                    "Qt Linguist</p>"
                    "<p>Desktop application to record the intake, diagnosis, repair and "
                    "delivery of equipment in a technical service workshop, with customers, "
                    "orders, budgets, payments, printable documents, user accounts and a "
                    "local SQLite database.</p>"
                    '<p><b>Repository</b><br><a href="https://github.com/wachin/'
                    'LucioTech-Service-Manager">https://github.com/wachin/'
                    "LucioTech-Service-Manager</a></p>"
                    "<p>Jipijapa, Manabí, Ecuador</p>"
                )
            )
        )
        right.addWidget(details, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        right.addWidget(buttons)

        layout.addLayout(left, 0)
        layout.addLayout(right, 1)

    def developer_card(self, name: str, email: str, facebook: str, photo_path: Path) -> QFrame:
        """Tarjeta con la foto, el nombre, el correo y el Facebook de un desarrollador."""
        card = QFrame()
        card.setObjectName("developerCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        photo = QLabel()
        photo.setObjectName("developerPhoto")
        photo.setFixedSize(88, 88)
        photo.setPixmap(self.rounded_photo(photo_path, 88, 10))
        photo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info = QLabel()
        info.setObjectName("aboutText")
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        info.setText(
            self.styled_links(
                f"<p><b>© 2026 {name}</b><br>"
                f'<a href="mailto:{email}">{email}</a><br>'
                f'<a href="{facebook}">{facebook.replace("https://www.", "")}</a></p>'
            )
        )

        layout.addWidget(photo)
        layout.addWidget(info, 1)
        return card

    def styled_links(self, html: str) -> str:
        link_style = 'style="color:#0645ad; text-decoration: underline; font-weight: 600;"'
        return html.replace("<a href=", f"<a {link_style} href=")

    def rounded_photo(self, photo_path: Path, size: int, radius: int) -> QPixmap:
        """Recorta la foto en cuadrado y le redondea las esquinas."""
        source = QPixmap(str(photo_path))
        if source.isNull():
            source = QPixmap(size, size)
            source.fill(Qt.GlobalColor.transparent)
        scaled_photo = source.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled_photo.width() - size) // 2)
        y = max(0, (scaled_photo.height() - size) // 2)
        cropped = scaled_photo.copy(x, y, size, size)
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, cropped)
        painter.end()
        return result
