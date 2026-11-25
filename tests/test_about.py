"""Pruebas del diálogo Ayuda ▸ Acerca de… y de los créditos del programa."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QLabel
from pytestqt.qtbot import QtBot
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import APP_CONFIG
from luciotech.ui.dialogs.about_dialog import (
    DEVELOPERS,
    PHOTOS_DIR,
    REPOSITORY_URL,
    AboutDialog,
)
from luciotech.ui.main_window import MainWindow


def _visible_text(dialog: AboutDialog) -> str:
    texts = [dialog.windowTitle()]
    texts.extend(label.text() for label in dialog.findChildren(QLabel))
    return " ".join(texts)


def test_about_dialog_shows_both_developer_cards(
    qtbot: QtBot, qapp: QApplication
) -> None:
    dialog = AboutDialog()
    qtbot.addWidget(dialog)
    text = _visible_text(dialog)
    assert dialog.windowTitle() == "Acerca de…"
    for name, email, facebook, _photo in DEVELOPERS:
        assert name in text
        assert email in text
        assert facebook in text
    assert text.count("© 2026") == 2


def test_about_dialog_credits_this_program(qtbot: QtBot, qapp: QApplication) -> None:
    dialog = AboutDialog()
    qtbot.addWidget(dialog)
    text = _visible_text(dialog)
    assert APP_CONFIG.app_name in text
    assert "GNU GPL v3" in text
    assert "SQLAlchemy" in text
    assert REPOSITORY_URL in text
    assert "Jipijapa, Manabí, Ecuador" in text


def test_developer_photos_ship_with_the_package() -> None:
    for *_rest, photo in DEVELOPERS:
        assert (PHOTOS_DIR / photo).is_file()


def test_main_window_offers_the_about_dialog_in_the_help_menu(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    window = MainWindow(session_factory)
    qtbot.addWidget(window)
    menus = {action.text(): action.menu() for action in window.menuBar().actions()}
    assert "&Ayuda" in menus
    assert [action.text() for action in menus["&Ayuda"].actions()] == ["&Acerca de…"]
