"""Entrada a la aplicación: acceso con usuario y contraseña, y creación del primer usuario (§19).

Son dos diálogos distintos porque son dos momentos distintos:

- `FirstUserDialog` sale una sola vez, la primera vez que se abre la aplicación en un equipo,
  cuando la tabla `usuarios` está vacía. No se pide una contraseña que nadie conoce: se crea la
  cuenta de administrador del taller.
- `LoginDialog` es el de todos los días: muestra los usuarios del taller en una lista
  desplegable, pide solo la contraseña y también permite dar de alta una cuenta nueva sin
  tener que entrar antes con la de un administrador. Esa alta desde el acceso crea siempre un
  técnico: si cualquiera pudiera elegir el rol, se daría administración a sí mismo sin saber
  ninguna contraseña.

Los dos devuelven en `self.user` un `CurrentUser`, que es lo que después viaja a la ventana, al
historial de las órdenes y al pie de los documentos.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from luciotech.config import APP_CONFIG, DEFAULT_USER
from luciotech.database.enums import UserRole
from luciotech.database.models import User
from luciotech.ui.dialogs.users_dialog import UserFormDialog
from luciotech.ui.labels import role_label
from luciotech.services.user_service import (
    CurrentUser,
    authenticate,
    change_own_password,
    create_first_admin,
    current_user_of,
    has_users,
    list_login_users,
    touch_login,
)

ERROR_STYLE = "color: #b00020;"


class LoginDialog(QDialog):
    """Lista las cuentas activas y pide la contraseña; deja la cuenta en `self.user`."""

    def __init__(
        self, session_factory: sessionmaker[Session], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self.user: CurrentUser | None = None
        self.attempts = 0

        self.setWindowTitle(self.tr("Sign in"))
        self.setMinimumWidth(420)

        title = QLabel(APP_CONFIG.app_name)
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 4)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            self.tr("Choose your user and enter your password to open the workshop.")
        )
        subtitle.setWordWrap(True)

        self._user_combo = QComboBox()
        self._user_combo.setMinimumWidth(260)
        self._reload_users()

        self._password = QLineEdit()
        self._password.setPlaceholderText(self.tr("Password"))
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._show_password = QCheckBox(self.tr("Show password"))
        self._show_password.toggled.connect(self._on_show_password)

        form = QFormLayout()
        form.addRow(self.tr("User"), self._user_combo)
        form.addRow(self.tr("Password"), self._password)

        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setStyleSheet(ERROR_STYLE)

        buttons = QDialogButtonBox()
        self._enter_button = buttons.addButton(
            self.tr("Sign in"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._enter_button.setDefault(True)
        buttons.addButton(self.tr("Quit"), QDialogButtonBox.ButtonRole.RejectRole)
        self._create_button = buttons.addButton(
            self.tr("New user…"), QDialogButtonBox.ButtonRole.ActionRole
        )
        self._create_button.clicked.connect(self._create_user)
        buttons.accepted.connect(self._attempt_login)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(self._show_password)
        layout.addWidget(self._message)
        layout.addWidget(buttons)

        self._password.setFocus(Qt.FocusReason.OtherFocusReason)

    def _on_show_password(self, shown: bool) -> None:
        self._password.setEchoMode(
            QLineEdit.EchoMode.Normal if shown else QLineEdit.EchoMode.Password
        )

    def _reload_users(self, selected: str | None = None) -> None:
        """Vuelve a llenar la lista con las cuentas activas y deja elegida la indicada."""
        self._user_combo.clear()
        with self._session_factory() as session:
            for index, user in enumerate(list_login_users(session)):
                label = user.nombre_completo or user.nombre_usuario
                self._user_combo.addItem(label, user.nombre_usuario)
                self._user_combo.setItemData(
                    index,
                    f"{user.nombre_usuario} · {role_label(user.rol)}",
                    Qt.ItemDataRole.ToolTipRole,
                )
        chosen = self._user_combo.findData(selected) if selected else -1
        self._user_combo.setCurrentIndex(max(chosen, 0))

    def _create_user(self) -> None:
        """Da de alta una cuenta de técnico sin salir del acceso y la deja lista para entrar."""
        dialog = UserFormDialog(
            self._session_factory, parent=self, fixed_role=UserRole.TECNICO
        )
        dialog.exec()
        if dialog.result() != QDialog.DialogCode.Accepted or not dialog.username:
            return
        self._reload_users(dialog.username)
        self._message.clear()
        self._password.clear()
        self._password.setFocus(Qt.FocusReason.OtherFocusReason)

    def _attempt_login(self) -> None:
        username = self._user_combo.currentData()
        password = self._password.text()
        if not username:
            self._message.setText(self.tr("There is no active user to sign in."))
            return
        if not password:
            self._message.setText(self.tr("Enter your password."))
            return
        self.attempts += 1
        try:
            with self._session_factory() as session:
                user = authenticate(session, username, password)
                if user is None:
                    self._message.setText(self.tr("Incorrect user or password."))
                    self._password.clear()
                    self._password.setFocus(Qt.FocusReason.OtherFocusReason)
                    return
                touch_login(session, user)
                session.commit()
                self.user = current_user_of(user)
        except SQLAlchemyError:
            self._message.setText(self.tr("Could not check the credentials. Please try again."))
            return
        self.accept()


class FirstUserDialog(QDialog):
    """Crea la cuenta de administrador cuando el equipo todavía no tiene usuarios."""

    def __init__(
        self, session_factory: sessionmaker[Session], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self.user: CurrentUser | None = None

        self.setWindowTitle(self.tr("Create the first user"))
        self.setMinimumWidth(460)

        title = QLabel(self.tr("Welcome to %1").replace("%1", APP_CONFIG.app_name))
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 4)
        title_font.setBold(True)
        title.setFont(title_font)

        explanation = QLabel(
            self.tr(
                "There is no account on this computer yet. Create the workshop administrator "
                "account: it will appear on the documents you print and it can add the other "
                "technicians later from File ▸ Users."
            )
        )
        explanation.setWordWrap(True)

        self._full_name = QLineEdit(DEFAULT_USER)
        self._full_name.setPlaceholderText(self.tr("First and last name, as it should be printed"))
        self._username = QLineEdit()
        self._username.setPlaceholderText(self.tr("Used to sign in; no spaces or accents"))
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._repeat = QLineEdit()
        self._repeat.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow(self.tr("Full name"), self._full_name)
        form.addRow(self.tr("User"), self._username)
        form.addRow(self.tr("Password"), self._password)
        form.addRow(self.tr("Repeat password"), self._repeat)

        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setStyleSheet(ERROR_STYLE)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addLayout(form)
        layout.addWidget(self._message)
        layout.addWidget(buttons)

        self._username.setFocus(Qt.FocusReason.OtherFocusReason)

    def _save(self) -> None:
        if self._password.text() != self._repeat.text():
            self._message.setText(self.tr("The two passwords do not match."))
            self._repeat.clear()
            self._repeat.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        try:
            with self._session_factory() as session:
                user = create_first_admin(
                    session,
                    username=self._username.text(),
                    full_name=self._full_name.text(),
                    password=self._password.text(),
                )
                session.commit()
                self.user = current_user_of(user)
        except ValueError as exc:
            self._message.setText(str(exc))
            return
        except SQLAlchemyError:
            self._message.setText(self.tr("The user could not be created. Please try again."))
            return
        self.accept()


class ChangePasswordDialog(QDialog):
    """Cambio de contraseña de la propia cuenta: pide la actual y la repite."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        user_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._user_id = user_id
        self.setWindowTitle(self.tr("Change my password"))
        self.setMinimumWidth(420)

        self._current = QLineEdit()
        self._current.setEchoMode(QLineEdit.EchoMode.Password)
        self._new = QLineEdit()
        self._new.setEchoMode(QLineEdit.EchoMode.Password)
        self._repeat = QLineEdit()
        self._repeat.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow(self.tr("Current password"), self._current)
        form.addRow(self.tr("New password"), self._new)
        form.addRow(self.tr("Repeat the new password"), self._repeat)

        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setStyleSheet(ERROR_STYLE)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._message)
        layout.addWidget(buttons)

        self._current.setFocus(Qt.FocusReason.OtherFocusReason)

    def _save(self) -> None:
        if self._new.text() != self._repeat.text():
            self._message.setText(self.tr("The two new passwords do not match."))
            return
        try:
            with self._session_factory() as session:
                user = session.get(User, self._user_id)
                if user is None:
                    self._message.setText(self.tr("The user no longer exists."))
                    return
                change_own_password(session, user, self._current.text(), self._new.text())
                session.commit()
        except ValueError as exc:
            self._message.setText(str(exc))
            return
        except SQLAlchemyError:
            self._message.setText(self.tr("The password could not be changed. Please try again."))
            return
        self.accept()


def login_user(
    session_factory: sessionmaker[Session], parent: QWidget | None = None
) -> CurrentUser | None:
    """Abre el diálogo que toca: crear el primer usuario o pedir el acceso.

    Devuelve `None` si el usuario cierra el diálogo sin entrar.
    """
    with session_factory() as session:
        first_time = not has_users(session)
    dialog = (
        FirstUserDialog(session_factory, parent)
        if first_time
        else LoginDialog(session_factory, parent)
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.user
