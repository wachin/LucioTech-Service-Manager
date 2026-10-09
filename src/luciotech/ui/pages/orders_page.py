"""Lista de órdenes con filtros básicos y acceso a nueva recepción (§10, alcance Fase 1)."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.enums import OrderState, Priority
from luciotech.services.order_query_service import OrderFilter, search_orders
from luciotech.services.settings_service import equipment_types
from luciotech.ui.dialogs.reception_dialog import ReceptionDialog
from luciotech.ui.formatting import format_datetime, format_money

ANY = ""
COLUMNS = (
    "Número de orden",
    "Fecha de ingreso",
    "Cliente",
    "Tipo de equipo",
    "Marca y modelo",
    "Estado",
    "Prioridad",
    "Total",
    "Saldo",
)


class OrdersPage(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, session_factory: sessionmaker[Session], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session_factory = session_factory

        self._text = QLineEdit()
        self._text.setPlaceholderText(self.tr("Número, cliente, teléfono, serie, marca o modelo"))
        self._text.setClearButtonEnabled(True)
        self._state = QComboBox()
        self._priority = QComboBox()
        self._equipment_type = QComboBox()
        self._only_balance = QCheckBox(self.tr("Con saldo pendiente"))
        self._new_button = QPushButton(self.tr("Nueva recepción"))
        self._new_button.clicked.connect(self._new_reception)

        self._state.addItem(self.tr("Todos los estados"), ANY)
        for state in OrderState:
            self._state.addItem(state.value, state.value)
        self._priority.addItem(self.tr("Todas las prioridades"), ANY)
        for priority in Priority:
            self._priority.addItem(priority.value, priority.value)

        filters = QHBoxLayout()
        filters.addWidget(self._text, 2)
        filters.addWidget(self._state)
        filters.addWidget(self._priority)
        filters.addWidget(self._equipment_type)
        filters.addWidget(self._only_balance)
        filters.addWidget(self._new_button)

        self._table = QTableWidget(0, len(COLUMNS))
        self._table.setHorizontalHeaderLabels([self.tr(c) for c in COLUMNS])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSortingEnabled(False)

        self._text.textChanged.connect(lambda _text: self.refresh())
        self._state.currentIndexChanged.connect(lambda _index: self.refresh())
        self._priority.currentIndexChanged.connect(lambda _index: self.refresh())
        self._equipment_type.currentIndexChanged.connect(lambda _index: self.refresh())
        self._only_balance.toggled.connect(lambda _checked: self.refresh())

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self._table)
        self._load_equipment_types()
        self.refresh()

    def _load_equipment_types(self) -> None:
        with self._session_factory() as session:
            types = equipment_types(session)
        self._equipment_type.clear()
        self._equipment_type.addItem(self.tr("Todos los tipos"), ANY)
        for tipo in types:
            self._equipment_type.addItem(tipo, tipo)

    def current_filter(self) -> OrderFilter:
        return OrderFilter(
            text=self._text.text(),
            estado=self._state.currentData() or None,
            prioridad=self._priority.currentData() or None,
            tipo_equipo=self._equipment_type.currentData() or None,
            solo_con_saldo=self._only_balance.isChecked(),
        )

    def refresh(self) -> None:
        with self._session_factory() as session:
            orders = search_orders(session, self.current_filter())
            rows = [
                [
                    order.numero_orden,
                    format_datetime(order.fecha_ingreso),
                    order.customer.nombre_completo,
                    order.equipment.tipo_equipo,
                    " ".join(part for part in (order.equipment.marca, order.equipment.modelo) if part),
                    order.estado,
                    order.prioridad,
                    format_money(order.total),
                    format_money(order.saldo_pendiente),
                ]
                for order in orders
            ]
        self._table.setRowCount(len(rows))
        for row, cells in enumerate(rows):
            for column, value in enumerate(cells):
                self._table.setItem(row, column, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()

    def visible_row_count(self) -> int:
        return self._table.rowCount()

    def order_number_at(self, row: int) -> str:
        item = self._table.item(row, 0)
        return item.text() if item is not None else ""

    def _new_reception(self) -> None:
        dialog = ReceptionDialog(self._session_factory, parent=self)
        if dialog.exec():
            self.refresh()
            self.data_changed.emit()
