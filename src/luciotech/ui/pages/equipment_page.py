"""Lista de equipos con acceso a alta y edición (§7.2).

La contraseña del equipo no se muestra en la lista.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from luciotech.database.repositories import CustomerRepository, EquipmentRepository
from luciotech.ui.dialogs.equipment_dialog import EquipmentDialog


class EquipmentPage(QWidget):
    data_changed = pyqtSignal()

    def __init__(
        self, session_factory: sessionmaker[Session], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory

        new_button = QPushButton(self.tr("Nuevo equipo"))
        new_button.clicked.connect(self._new_equipment)
        edit_button = QPushButton(self.tr("Editar"))
        edit_button.clicked.connect(self._edit_selected)

        toolbar = QHBoxLayout()
        toolbar.addStretch(1)
        toolbar.addWidget(new_button)
        toolbar.addWidget(edit_button)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            [
                self.tr("Cliente"),
                self.tr("Tipo de equipo"),
                self.tr("Marca"),
                self.tr("Modelo"),
                self.tr("Número de serie"),
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
            rows = [
                (
                    equipment.id,
                    [
                        equipment.customer.nombre_completo,
                        equipment.tipo_equipo,
                        equipment.marca or "",
                        equipment.modelo or "",
                        equipment.numero_serie or "",
                    ],
                )
                for equipment in EquipmentRepository(session).list_all()
            ]
        self._table.setRowCount(len(rows))
        for row, (equipment_id, cells) in enumerate(rows):
            for column, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, equipment_id)
                self._table.setItem(row, column, item)

    def visible_row_count(self) -> int:
        return self._table.rowCount()

    def _has_customers(self) -> bool:
        with self._session_factory() as session:
            return bool(CustomerRepository(session).list_all())

    def _new_equipment(self) -> None:
        if not self._has_customers():
            QMessageBox.information(
                self,
                self.tr("Nuevo equipo"),
                self.tr("Primero registre un cliente en la pestaña Clientes."),
            )
            return
        dialog = EquipmentDialog(self._session_factory, parent=self)
        if dialog.exec():
            self.data_changed.emit()

    def _edit_selected(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, self.tr("Editar equipo"), self.tr("Seleccione un equipo en la lista.")
            )
            return
        equipment_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = EquipmentDialog(self._session_factory, equipment_id=equipment_id, parent=self)
        if dialog.exec():
            self.data_changed.emit()
