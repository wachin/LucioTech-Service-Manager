"""Selector de documentos imprimibles de una orden (§13.1).

La ventana de la orden no imprime siempre lo mismo: primero se elige el documento y después
se abre su vista previa. Así el botón deja de llamarse «Imprimir comprobante» y pasa a ser
«Documentos».
"""

from __future__ import annotations

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from luciotech.ui.documents import DocumentKind, document_label

DESCRIPTIONS: dict[DocumentKind, str] = {
    DocumentKind.RECEPCION: (
        "Handed to the customer when the equipment is left: details, physical condition, "
        "accessories, photographs, amounts and service conditions."
    ),
    DocumentKind.PRESUPUESTO: (
        "Itemised quantities and prices, total, validity, terms and warranty, plus room for "
        "the customer's approval."
    ),
    DocumentKind.INFORME: (
        "Diagnosis, work performed, parts, recommendations, photographs, warranty coverage "
        "and warranty terms."
    ),
    DocumentKind.ENTREGA: (
        "Handed over when the equipment is returned: work performed, payments, balance, "
        "warranty, terms and declaration of conformity."
    ),
    DocumentKind.HISTORIAL: (
        "Every status change, note and payment of the order in chronological order."
    ),
}


class DocumentChooserDialog(QDialog):
    """Lista los documentos de la orden y devuelve el elegido."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Order documents"))
        self.setMinimumSize(520, 380)

        self._list = QListWidget()
        for kind in DocumentKind:
            item = QListWidgetItem(document_label(kind))
            item.setData(Qt.ItemDataRole.UserRole, kind.value)
            item.setToolTip(self.tr(DESCRIPTIONS[kind]))
            self._list.addItem(item)
        self._list.setCurrentRow(0)
        self._list.currentItemChanged.connect(self._show_description)
        self._list.itemDoubleClicked.connect(lambda _item: self.accept())

        self._description = QLabel()
        self._description.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Choose the document to print or save:")))
        layout.addWidget(self._list, 1)
        layout.addWidget(self._description)
        layout.addWidget(buttons)
        self._show_description()

    def selected_kind(self) -> DocumentKind:
        item = self._list.currentItem()
        assert item is not None
        return DocumentKind(item.data(Qt.ItemDataRole.UserRole))

    def select(self, kind: DocumentKind) -> None:
        """Deja elegido un documento concreto (lo usan las pruebas y los atajos)."""
        for row in range(self._list.count()):
            if self._list.item(row).data(Qt.ItemDataRole.UserRole) == kind.value:
                self._list.setCurrentRow(row)
                return

    def _show_description(self, *_args: object) -> None:
        item = self._list.currentItem()
        if item is None:
            self._description.setText("")
            return
        kind = DocumentKind(item.data(Qt.ItemDataRole.UserRole))
        self._description.setText(self.tr(DESCRIPTIONS[kind]))

    @classmethod
    def choose(cls, parent: QWidget | None = None) -> DocumentKind | None:
        """Abre el selector y devuelve el documento elegido, o None si se cancela."""
        dialog = cls(parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.selected_kind()


def _catalog() -> None:
    """Mantiene los textos en el catálogo de pylupdate6; no se ejecuta nunca."""
    QCoreApplication.translate(
        "DocumentChooserDialog",
        "Handed to the customer when the equipment is left: details, physical condition, "
        "accessories, photographs, amounts and service conditions.",
    )
    QCoreApplication.translate(
        "DocumentChooserDialog",
        "Itemised quantities and prices, total, validity, terms and warranty, plus room for "
        "the customer's approval.",
    )
    QCoreApplication.translate(
        "DocumentChooserDialog",
        "Diagnosis, work performed, parts, recommendations, photographs, warranty coverage "
        "and warranty terms.",
    )
    QCoreApplication.translate(
        "DocumentChooserDialog",
        "Handed over when the equipment is returned: work performed, payments, balance, "
        "warranty, terms and declaration of conformity.",
    )
    QCoreApplication.translate(
        "DocumentChooserDialog",
        "Every status change, note and payment of the order in chronological order.",
    )
