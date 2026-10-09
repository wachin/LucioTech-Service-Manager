"""Lista de clientes con búsqueda y acceso a alta y edición (§7.1)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.repositories import CustomerRepository
from luciotech.ui.dialogs.customer_dialog import CustomerDialog

SEARCH_COLUMNS = 3


class CustomersPage(QWidget):
    data_changed = pyqtSignal()

    def __init__(
        self, session_factory: sessionmaker[Session], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._rows: list[tuple[int, list[str]]] = []

        self._search = QLineEdit()
        self._search.setPlaceholderText(self.tr("Buscar por nombre, identificación o teléfono"))
        self._search.textChanged.connect(self._apply_filter)

        new_button = QPushButton(self.tr("Nuevo cliente"))
        new_button.clicked.connect(self._new_customer)
        edit_button = QPushButton(self.tr("Editar"))
        edit_button.clicked.connect(self._edit_selected)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self._search, 1)
        toolbar.addWidget(new_button)
        toolbar.addWidget(edit_button)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            [
                self.tr("Nombre completo"),
                self.tr("Identificación"),
                self.tr("Teléfono"),
                self.tr("Correo electrónico"),
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.doubleClicked.connect(lambda _index: self._edit_selected())

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self._table)
        self.refresh()

    def refresh(self) -> None:
        with self._session_factory() as session:
            self._rows = [
                (
                    customer.id,
                    [
                        customer.nombre_completo,
                        customer.numero_identificacion or "",
                        customer.telefono_principal or "",
                        customer.correo_electronico or "",
                    ],
                )
                for customer in CustomerRepository(session).list_all()
            ]
        self._apply_filter(self._search.text())

    def visible_row_count(self) -> int:
        return self._table.rowCount()

    def search_text(self) -> str:
        return self._search.text()

    def set_search_text(self, text: str) -> None:
        self._search.setText(text)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        visible = [
            (customer_id, cells)
            for customer_id, cells in self._rows
            if not needle or any(needle in cell.lower() for cell in cells[:SEARCH_COLUMNS])
        ]
        self._table.setRowCount(len(visible))
        for row, (customer_id, cells) in enumerate(visible):
            for column, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, customer_id)
                self._table.setItem(row, column, item)

    def _new_customer(self) -> None:
        dialog = CustomerDialog(self._session_factory, parent=self)
        if dialog.exec():
            self.data_changed.emit()

    def _edit_selected(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, self.tr("Editar cliente"), self.tr("Seleccione un cliente en la lista.")
            )
            return
        customer_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = CustomerDialog(self._session_factory, customer_id=customer_id, parent=self)
        if dialog.exec():
            self.data_changed.emit()
