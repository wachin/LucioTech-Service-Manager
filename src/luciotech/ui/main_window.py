"""Ventana principal con pestañas Inicio, Clientes y Equipos (§6, §9 y §17)."""

from __future__ import annotations

from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import APP_CONFIG
from luciotech.ui.pages.customers_page import CustomersPage
from luciotech.ui.pages.equipment_page import EquipmentPage
from luciotech.ui.pages.home_page import HomePage
from luciotech.ui.pages.orders_page import OrdersPage


class MainWindow(QMainWindow):
    def __init__(
        self, session_factory: sessionmaker[Session], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_CONFIG.app_name)
        self.resize(1200, 720)

        self._home = HomePage(session_factory)
        self._customers = CustomersPage(session_factory)
        self._equipment = EquipmentPage(session_factory)
        self._orders = OrdersPage(session_factory)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._home, self.tr("Inicio"))
        self._tabs.addTab(self._orders, self.tr("Órdenes"))
        self._tabs.addTab(self._customers, self.tr("Clientes"))
        self._tabs.addTab(self._equipment, self.tr("Equipos"))
        self.setCentralWidget(self._tabs)

        self._customers.data_changed.connect(self.refresh_all)
        self._equipment.data_changed.connect(self.refresh_all)
        self._orders.data_changed.connect(self.refresh_all)
        self._tabs.currentChanged.connect(lambda _index: self.refresh_all())

        self._build_menu()
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_all)

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

    def refresh_all(self) -> None:
        self._home.refresh()
        self._orders.refresh()
        self._customers.refresh()
        self._equipment.refresh()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&Archivo"))
        quit_action = QAction(self.tr("&Salir"), self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
