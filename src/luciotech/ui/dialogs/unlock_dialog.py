"""Desbloqueo de la sesión tras un periodo de inactividad (§19).

La ventana principal abre este diálogo cuando nadie ha tocado el teclado ni el ratón durante
el tiempo configurado. Solo se cierra con la contraseña de la cuenta que tiene la sesión
abierta: no hay botón de cancelar ni de cerrar, porque el sentido del bloqueo es que lo que
hay detrás deje de estar a la vista de quien pase por delante del mostrador.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.models import User
from luciotech.services.user_service import CurrentUser, verify_password

ERROR_STYLE = "color: #b00020;"


class UnlockDialog(QDialog):
    """Pide la contraseña de la cuenta de la sesión para volver al trabajo."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        user: CurrentUser,
        minutes: int,
        parent: QWidget | None = None,
    ) -> None:
        """Prepara el aviso de bloqueo para `user`, que llevaba `minutes` sin actividad."""
        super().__init__(parent)
        self._session_factory = session_factory
        self._user_id = user.id
        self._user_name = user.display_name
        self.setWindowTitle(self.tr("Session locked"))
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumWidth(420)
        self.setModal(True)

        title = QLabel(self.tr("Session locked"))
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 3)
        title_font.setBold(True)
        title.setFont(title_font)

        explanation = QLabel(
            self.tr("The session was locked after %1 minutes without activity.").replace(
                "%1", str(minutes)
            )
        )
        explanation.setWordWrap(True)

        who = QLabel(
            self.tr("Enter the password of %1 to continue.").replace("%1", self._user_name)
        )
        who.setWordWrap(True)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        form = QFormLayout()
        form.addRow(self.tr("Password"), self._password)

        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setStyleSheet(ERROR_STYLE)

        buttons = QDialogButtonBox()
        self._unlock_button = buttons.addButton(
            self.tr("Unlock"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._unlock_button.setDefault(True)
        buttons.accepted.connect(self._unlock)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addWidget(who)
        layout.addLayout(form)
        layout.addWidget(self._message)
        layout.addWidget(buttons)

        self._password.setFocus(Qt.FocusReason.OtherFocusReason)

    def _unlock(self) -> None:
        """Comprueba la contraseña; solo con la correcta se cierra el bloqueo."""
        if self._user_id is None:
            self.accept()
            return
        try:
            with self._session_factory() as session:
                user = session.get(User, self._user_id)
                if user is None or not verify_password(
                    self._password.text(), user.contrasena_hash
                ):
                    self._message.setText(self.tr("Incorrect password."))
                    self._password.clear()
                    self._password.setFocus(Qt.FocusReason.OtherFocusReason)
                    return
        except SQLAlchemyError:
            self._message.setText(
                self.tr("The password could not be checked. Please try again.")
            )
            return
        self.accept()

    def reject(self) -> None:
        """El bloqueo no se quita con Escape ni con el botón de cancelar."""
        self._password.clear()
        self._password.setFocus(Qt.FocusReason.OtherFocusReason)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (nombre de Qt)
        """Cerrar la ventana no desbloquea la sesión."""
        event.ignore()
