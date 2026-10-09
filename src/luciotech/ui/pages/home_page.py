"""Panel de inicio con tarjetas de conteos (§6)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import DEFAULT_CURRENCY
from luciotech.services.dashboard_service import DashboardCounts, dashboard_counts

CARDS_PER_ROW = 4


class HomePage(QWidget):
    def __init__(
        self, session_factory: sessionmaker[Session], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._values: dict[str, QLabel] = {}

        title = QLabel(self.tr("Resumen del taller"))
        title_font = title.font()
        title_font.setPointSizeF(title_font.pointSizeF() * 1.4)
        title_font.setBold(True)
        title.setFont(title_font)

        grid = QGridLayout()
        for index, (key, caption) in enumerate(self._card_specs()):
            card, value = self._make_card(caption)
            self._values[key] = value
            grid.addWidget(card, index // CARDS_PER_ROW, index % CARDS_PER_ROW)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(grid)
        layout.addStretch(1)
        self.refresh()

    def value_text(self, key: str) -> str:
        return self._values[key].text()

    def refresh(self) -> None:
        with self._session_factory() as session:
            counts = dashboard_counts(session, date.today())
        self._show(counts)

    def _card_specs(self) -> list[tuple[str, str]]:
        return [
            ("received_today", self.tr("Equipos recibidos hoy")),
            ("pending_diagnosis", self.tr("Pendientes de diagnóstico")),
            ("under_repair", self.tr("En reparación")),
            ("awaiting_approval", self.tr("Esperando aprobación")),
            ("ready_for_delivery", self.tr("Listos para entregar")),
            ("delivered_this_month", self.tr("Entregados este mes")),
            ("outstanding_balance", self.tr("Saldo pendiente")),
            ("monthly_income", self.tr("Ingresos del mes")),
        ]

    def _make_card(self, caption: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        caption_label = QLabel(caption)
        caption_label.setWordWrap(True)
        value_label = QLabel("–")
        value_font = value_label.font()
        value_font.setPointSizeF(value_font.pointSizeF() * 1.6)
        value_font.setBold(True)
        value_label.setFont(value_font)
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(caption_label)
        card_layout.addWidget(value_label)
        return card, value_label

    def _show(self, counts: DashboardCounts) -> None:
        self._values["received_today"].setText(str(counts.received_today))
        self._values["pending_diagnosis"].setText(str(counts.pending_diagnosis))
        self._values["under_repair"].setText(str(counts.under_repair))
        self._values["awaiting_approval"].setText(str(counts.awaiting_approval))
        self._values["ready_for_delivery"].setText(str(counts.ready_for_delivery))
        self._values["delivered_this_month"].setText(str(counts.delivered_this_month))
        self._values["outstanding_balance"].setText(_money(counts.outstanding_balance))
        self._values["monthly_income"].setText(_money(counts.monthly_income))


def _money(amount: Decimal) -> str:
    return f"{amount:,.2f} {DEFAULT_CURRENCY}"
