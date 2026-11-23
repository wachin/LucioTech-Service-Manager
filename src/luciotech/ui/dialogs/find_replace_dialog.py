"""Diálogo de buscar y reemplazar para el editor de texto enriquecido (§8)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from luciotech.ui.widgets.rich_text_editor import RichTextEditor


class FindReplaceDialog(QDialog):
    def __init__(self, editor: RichTextEditor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self.setWindowTitle(self.tr("Find and replace"))
        self.setMinimumWidth(380)

        self._find_field = QLineEdit()
        self._find_field.setPlaceholderText(self.tr("Text to find"))
        self._replace_field = QLineEdit()
        self._replace_field.setPlaceholderText(self.tr("Replace with"))
        self._case_check = QCheckBox(self.tr("Match case"))
        self._status = QLabel()

        find_button = QPushButton(self.tr("Find next"))
        find_button.clicked.connect(self._on_find_next)
        replace_button = QPushButton(self.tr("Replace"))
        replace_button.clicked.connect(self._on_replace)
        replace_all_button = QPushButton(self.tr("Replace all"))
        replace_all_button.clicked.connect(self._on_replace_all)
        close_button = QPushButton(self.tr("Close"))
        close_button.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow(self.tr("Find"), self._find_field)
        form.addRow(self.tr("Replace with"), self._replace_field)
        form.addRow(self._case_check)

        buttons = QHBoxLayout()
        buttons.addWidget(find_button)
        buttons.addWidget(replace_button)
        buttons.addWidget(replace_all_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._status)
        layout.addLayout(buttons)
        self._find_field.setFocus()

    def _case_sensitive(self) -> bool:
        return self._case_check.isChecked()

    def _on_find_next(self) -> None:
        found = self._editor.find_next(self._find_field.text(), self._case_sensitive())
        self._status.setText(
            self.tr("Match found.") if found else self.tr("No more matches.")
        )

    def _on_replace(self) -> None:
        done = self._editor.replace_current(
            self._find_field.text(), self._replace_field.text(), self._case_sensitive()
        )
        if done:
            self._status.setText(self.tr("Replaced."))
        else:
            self._on_find_next()

    def _on_replace_all(self) -> None:
        count = self._editor.replace_all(
            self._find_field.text(), self._replace_field.text(), self._case_sensitive()
        )
        self._status.setText(self.tr("%1 replacements.").replace("%1", str(count)))
