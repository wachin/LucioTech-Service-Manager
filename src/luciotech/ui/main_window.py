"""Ventana principal con pestañas Inicio, Órdenes, Clientes, Equipos y Papelera (§6, §9, §17 y §18).

La ventana sabe quién tiene la sesión abierta (`CurrentUser`): ese nombre es el que va a la
barra de estado, al historial de cada orden y al pie de los documentos que se imprimen.
"""

from __future__ import annotations

from time import monotonic

from PyQt6.QtCore import QEvent, QObject, QTimer, Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMainWindow,
    QTabWidget,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import APP_CONFIG, INACTIVITY_LOCK_MINUTES
from luciotech.services.settings_service import tax_settings
from luciotech.services.totals_service import recalculate_stored_totals
from luciotech.services.user_service import DEFAULT_CURRENT_USER, CurrentUser
from luciotech.ui.dialogs.about_dialog import AboutDialog
from luciotech.ui.dialogs.login_dialog import ChangePasswordDialog
from luciotech.ui.dialogs.settings_dialog import SettingsDialog
from luciotech.ui.dialogs.unlock_dialog import UnlockDialog
from luciotech.ui.dialogs.users_dialog import UsersDialog
from luciotech.ui.labels import role_label
from luciotech.ui.pages.customers_page import CustomersPage
from luciotech.ui.pages.equipment_page import EquipmentPage
from luciotech.ui.pages.home_page import HomePage
from luciotech.ui.pages.orders_page import OrdersPage
from luciotech.ui.pages.trash_page import TrashPage

MIN_WIDTH = 800
MIN_HEIGHT = 560

# Cada segundo se compara el reloj con la última vez que hubo teclado o ratón. El evento
# que cuenta como actividad se filtra en toda la aplicación, así que escribir en un diálogo
# también mantiene la sesión despierta.
ACTIVITY_CHECK_MS = 1000
ACTIVITY_EVENTS = frozenset(
    {
        QEvent.Type.KeyPress,
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonDblClick,
        QEvent.Type.MouseMove,
        QEvent.Type.Wheel,
    }
)


class MainWindow(QMainWindow):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        user: CurrentUser | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._user = user or DEFAULT_CURRENT_USER
        self.logout_requested = False
        self.setWindowTitle(APP_CONFIG.app_name)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

        self._home = HomePage(session_factory)
        self._customers = CustomersPage(session_factory)
        self._equipment = EquipmentPage(session_factory)
        self._orders = OrdersPage(session_factory, usuario=self._user.display_name)
        self._trash = TrashPage(session_factory, usuario=self._user.display_name)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._home, self.tr("Home"))
        self._tabs.addTab(self._orders, self.tr("Orders"))
        self._tabs.addTab(self._customers, self.tr("Customers"))
        self._tabs.addTab(self._equipment, self.tr("Equipment"))
        self._tabs.addTab(self._trash, self.tr("Trash"))
        self.setCentralWidget(self._tabs)

        self._customers.data_changed.connect(self.refresh_all)
        self._equipment.data_changed.connect(self.refresh_all)
        self._orders.data_changed.connect(self.refresh_all)
        self._trash.data_changed.connect(self.refresh_all)
        self._tabs.currentChanged.connect(lambda _index: self.refresh_all())

        self._build_menu()
        self._show_session()
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_all)

        self._last_activity = monotonic()
        self._unlocking = False
        self._lock_timer = QTimer(self)
        self._lock_timer.setInterval(ACTIVITY_CHECK_MS)
        self._lock_timer.timeout.connect(self._check_inactivity)
        # La cuenta de respaldo de las pruebas y del arranque sin sesión no tiene contraseña
        # que pedir, así que no se bloquea.
        if self._user.id is not None:
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
            self._lock_timer.start()

    @property
    def user(self) -> CurrentUser:
        return self._user

    @property
    def home_page(self) -> HomePage:
        return self._home

    @property
    def customers_page(self) -> CustomersPage:
        return self._customers

    @property
    def equipment_page(self) -> EquipmentPage:
        return self._equipment

    @property
    def orders_page(self) -> OrdersPage:
        return self._orders

    @property
    def trash_page(self) -> TrashPage:
        return self._trash

    def refresh_all(self) -> None:
        self._home.refresh()
        self._orders.refresh()
        self._customers.refresh()
        self._equipment.refresh()
        self._trash.refresh()

    def _show_session(self) -> None:
        """Quién está dentro, a la vista y sin ocupar sitio en la barra de pestañas."""
        label = QLabel(
            self.tr("Signed in: %1 · %2")
            .replace("%1", self._user.display_name)
            .replace("%2", role_label(self._user.role))
        )
        label.setToolTip(
            self.tr(
                "This name appears in the order history and in the footer of the documents "
                "you print."
            )
        )
        self.statusBar().addPermanentWidget(label)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&File"))
        if self._user.id is not None:
            password_action = QAction(self.tr("Change &my password…"), self)
            password_action.triggered.connect(self._change_password)
            file_menu.addAction(password_action)
        if self._user.is_admin:
            settings_action = QAction(self.tr("&Settings…"), self)
            settings_action.triggered.connect(self._open_settings)
            file_menu.addAction(settings_action)
            users_action = QAction(self.tr("&Users…"), self)
            users_action.setShortcut(QKeySequence("Ctrl+U"))
            users_action.triggered.connect(self._open_users)
            file_menu.addAction(users_action)
        if self._user.id is not None:
            logout_action = QAction(self.tr("&Sign out"), self)
            logout_action.triggered.connect(self._logout)
            file_menu.addAction(logout_action)
        file_menu.addSeparator()
        quit_action = QAction(self.tr("&Quit"), self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        about_action = QAction(self.tr("&About…"), self)
        about_action.triggered.connect(self._open_about)
        help_menu.addAction(about_action)

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._session_factory, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        # Cambiar el IVA desde aquí debe recalcular las columnas guardadas igual que al arrancar.
        with self._session_factory() as session:
            if recalculate_stored_totals(session, tax_settings(session)):
                session.commit()
        self.refresh_all()

    def _open_users(self) -> None:
        UsersDialog(self._session_factory, self._user, parent=self).exec()
        self.refresh_all()

    def _change_password(self) -> None:
        if self._user.id is None:
            return
        ChangePasswordDialog(self._session_factory, self._user.id, parent=self).exec()

    def _logout(self) -> None:
        self.logout_requested = True
        self.close()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        """Cada tecla, clic o rueda reinicia la cuenta atrás de la inactividad."""
        if event.type() in ACTIVITY_EVENTS:
            self._last_activity = monotonic()
        return super().eventFilter(watched, event)

    def _can_lock(self) -> bool:
        """No se bloquea encima de un diálogo modal ni con un menú desplegable abierto."""
        if not self.isVisible() or self._unlocking:
            return False
        app = QApplication.instance()
        if app is None:
            return True
        return (
            app.activeModalWidget() is None
            and app.activePopupWidget() is None
        )

    def _check_inactivity(self) -> None:
        """Que el aviso de bloqueo no salte en mitad de un diálogo o de una vista previa."""
        if not self._can_lock():
            # Mientras haya un diálogo abierto se reinicia la cuenta: al cerrarlo, el
            # usuario vuelve a tener el periodo completo, no medio minuto.
            self._last_activity = monotonic()
            return
        if monotonic() - self._last_activity < INACTIVITY_LOCK_MINUTES * 60:
            return
        self._lock_session()

    def _lock_session(self) -> None:
        """Tapa la ventana con el diálogo de desbloqueo y no sigue hasta la contraseña."""
        self._unlocking = True
        self._lock_timer.stop()
        try:
            UnlockDialog(
                self._session_factory,
                self._user,
                INACTIVITY_LOCK_MINUTES,
                parent=self,
            ).exec()
        finally:
            self._last_activity = monotonic()
            self._unlocking = False
            if self._user.id is not None and self.isVisible():
                self._lock_timer.start()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (nombre de Qt)
        """Al cerrar la ventana se deja de escuchar la actividad de toda la aplicación."""
        self._lock_timer.stop()
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)
