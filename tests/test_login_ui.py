"""Diálogos de acceso y de gestión de usuarios (§19)."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox
from time import monotonic
from pytestqt.qtbot import QtBot
from sqlalchemy.orm import Session, sessionmaker

from luciotech.config import INACTIVITY_LOCK_MINUTES
from luciotech.database.enums import UserAuditAction, UserRole
from luciotech.services.user_service import (
    CurrentUser,
    authenticate,
    count_users,
    create_user,
    get_user,
    list_user_events,
    list_users,
    set_active,
    set_password,
)
from luciotech.ui.dialogs.login_dialog import (
    ChangePasswordDialog,
    FirstUserDialog,
    LoginDialog,
)
from luciotech.ui.dialogs.unlock_dialog import UnlockDialog
from luciotech.ui.dialogs.users_dialog import (
    SetPasswordDialog,
    UserFormDialog,
    UsersDialog,
)
from luciotech.ui.main_window import MainWindow

PASSWORD = "taller2026"


def _seed(session_factory: sessionmaker[Session]) -> CurrentUser:
    with session_factory() as session:
        user = create_user(
            session,
            username="ana",
            full_name="Ana Torres",
            password=PASSWORD,
            role=UserRole.ADMINISTRADOR,
        )
        session.commit()
        return CurrentUser(user.id, user.nombre_usuario, user.nombre_completo, user.rol)


# Primer arranque


def test_the_first_user_dialog_creates_the_admin_account(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    dialog = FirstUserDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._full_name.setText("Ing. Lucio")
    dialog._username.setText("lucio")
    dialog._password.setText(PASSWORD)
    dialog._repeat.setText(PASSWORD)

    dialog._save()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.user is not None
    assert dialog.user.is_admin is True
    assert dialog.user.display_name == "Ing. Lucio"
    assert count_users(_session(session_factory)) == 1


def test_the_first_user_dialog_asks_for_the_same_password_twice(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    dialog = FirstUserDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._full_name.setText("Ing. Lucio")
    dialog._username.setText("lucio")
    dialog._password.setText(PASSWORD)
    dialog._repeat.setText("otra cosa")

    dialog._save()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "no coinciden" in dialog._message.text()
    assert count_users(_session(session_factory)) == 0


def _session(session_factory: sessionmaker[Session]) -> Session:
    return session_factory()


# Acceso


def test_login_accepts_the_right_password_and_notes_the_access(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._user_combo.setCurrentIndex(dialog._user_combo.findData("ana"))
    dialog._password.setText(PASSWORD)

    dialog._attempt_login()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.user is not None
    assert dialog.user.display_name == "Ana Torres"
    with session_factory() as session:
        assert get_user(session, "ana").ultimo_acceso is not None


def test_login_rejects_a_wrong_password_and_keeps_the_window_open(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._user_combo.setCurrentIndex(dialog._user_combo.findData("ana"))
    dialog._password.setText("no es esta")

    dialog._attempt_login()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.user is None
    assert "incorrectos" in dialog._message.text()
    assert dialog._password.text() == ""
    assert dialog.attempts == 1


def test_login_complains_when_a_field_is_empty(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._user_combo.setCurrentIndex(dialog._user_combo.findData("ana"))

    dialog._attempt_login()

    assert "Escriba" in dialog._message.text()
    assert dialog.attempts == 0


def test_login_can_show_the_password_while_typing(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    assert dialog._password.echoMode() == QLineEdit.EchoMode.Password

    dialog._show_password.setChecked(True)

    assert dialog._password.echoMode() == QLineEdit.EchoMode.Normal


# La lista desplegable de usuarios


def test_login_lists_the_active_users_by_their_full_name(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    with session_factory() as session:
        create_user(session, username="luis", full_name="Luis Paredes", password=PASSWORD)
        session.commit()

    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)

    combo = dialog._user_combo
    assert combo.count() == 2
    assert [combo.itemText(index) for index in range(combo.count())] == [
        "Ana Torres",
        "Luis Paredes",
    ]
    assert [combo.itemData(index) for index in range(combo.count())] == ["ana", "luis"]
    assert combo.currentIndex() == 0


def test_login_hides_deactivated_accounts(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    with session_factory() as session:
        luis = create_user(
            session, username="luis", full_name="Luis Paredes", password=PASSWORD
        )
        session.commit()
        set_active(session, luis, False)
        session.commit()

    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)

    assert dialog._user_combo.count() == 1
    assert dialog._user_combo.itemData(0) == "ana"


def test_login_offers_first_the_account_that_signed_in_last(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    with session_factory() as session:
        create_user(session, username="luis", full_name="Luis Paredes", password=PASSWORD)
        session.commit()

    first = LoginDialog(session_factory)
    qtbot.addWidget(first)
    first._user_combo.setCurrentIndex(first._user_combo.findData("luis"))
    first._password.setText(PASSWORD)
    first._attempt_login()
    assert first.result() == QDialog.DialogCode.Accepted

    again = LoginDialog(session_factory)
    qtbot.addWidget(again)
    assert again._user_combo.itemData(0) == "luis"


def test_login_enters_with_the_chosen_account(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    with session_factory() as session:
        create_user(session, username="luis", full_name="Luis Paredes", password=PASSWORD)
        session.commit()

    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._user_combo.setCurrentIndex(dialog._user_combo.findData("luis"))
    dialog._password.setText(PASSWORD)
    dialog._attempt_login()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.user is not None
    assert dialog.user.username == "luis"
    assert dialog.user.display_name == "Luis Paredes"


def test_a_new_user_can_be_created_from_the_login_window(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(session_factory)
    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    assert dialog._user_combo.count() == 1

    def fill_and_save(form: UserFormDialog) -> None:
        form._full_name.setText("Luis Paredes")
        form._username.setText("luis")
        form._password.setText("1234")
        form._repeat.setText("1234")
        # El acceso no deja elegir rol: aunque se cambie por código, se guarda técnico.
        assert form._role.isEnabled() is False
        assert form._role.currentData() == UserRole.TECNICO.value
        form._role.setEnabled(True)
        form._role.setCurrentIndex(form._role.findData(UserRole.ADMINISTRADOR.value))
        form._save()

    monkeypatch.setattr(UserFormDialog, "exec", fill_and_save)

    dialog._create_user()

    assert dialog._user_combo.count() == 2
    assert dialog._user_combo.currentData() == "luis"
    assert dialog._password.text() == ""
    with session_factory() as session:
        user = get_user(session, "luis")
        assert user is not None
        assert user.rol == UserRole.TECNICO.value
        assert authenticate(session, "luis", "1234") is not None


def test_a_temporary_password_must_be_changed_before_entering(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        luis = create_user(
            session, username="luis", full_name="Luis Paredes", password=PASSWORD
        )
        session.flush()
        set_password(session, luis, "temporal1", actor=admin)
        session.commit()

    def change_it(dialog: ChangePasswordDialog) -> int:
        assert dialog.windowTitle() == "Cambie su contraseña"
        dialog._current.setText("temporal1")
        dialog._new.setText("propia2026")
        dialog._repeat.setText("propia2026")
        dialog._save()
        return dialog.result()

    monkeypatch.setattr(ChangePasswordDialog, "exec", change_it)

    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._user_combo.setCurrentIndex(dialog._user_combo.findData("luis"))
    dialog._password.setText("temporal1")

    dialog._attempt_login()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.user is not None
    with session_factory() as session:
        user = get_user(session, "luis")
        assert user is not None
        assert user.debe_cambiar_contrasena is False
        assert authenticate(session, "luis", "propia2026") is not None
        assert authenticate(session, "luis", "temporal1") is None


def test_cancelling_the_forced_change_keeps_the_login_window(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        luis = create_user(
            session, username="luis", full_name="Luis Paredes", password=PASSWORD
        )
        session.flush()
        set_password(session, luis, "temporal1", actor=admin)
        session.commit()

    monkeypatch.setattr(
        ChangePasswordDialog, "exec", lambda _dialog: QDialog.DialogCode.Rejected
    )

    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._user_combo.setCurrentIndex(dialog._user_combo.findData("luis"))
    dialog._password.setText("temporal1")

    dialog._attempt_login()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.user is None
    assert "Debe elegir" in dialog._message.text()
    with session_factory() as session:
        assert get_user(session, "luis").debe_cambiar_contrasena is True


def test_login_explains_when_no_active_account_is_left(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    with session_factory() as session:
        get_user(session, "ana").activo = False
        session.commit()

    dialog = LoginDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._password.setText(PASSWORD)

    dialog._attempt_login()

    assert "ningún usuario activo" in dialog._message.text()
    assert dialog.attempts == 0


# Gestión de usuarios


def test_the_users_dialog_lists_the_accounts(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        create_user(session, username="luis", full_name="Luis Paredes", password=PASSWORD)
        session.commit()

    dialog = UsersDialog(session_factory, admin)
    qtbot.addWidget(dialog)

    assert dialog._table.rowCount() == 2
    assert dialog._table.item(0, 0).text() == "ana"
    assert dialog._table.item(0, 2).text() == UserRole.ADMINISTRADOR.value


def test_the_users_dialog_shows_the_activity_log(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        create_user(
            session,
            username="luis",
            full_name="Luis Paredes",
            password=PASSWORD,
            actor=admin,
        )
        session.commit()

    dialog = UsersDialog(session_factory, admin)
    qtbot.addWidget(dialog)

    assert dialog._tabs.tabText(0) == "Usuarios"
    assert dialog._tabs.tabText(1) == "Actividad"
    assert dialog._activity.rowCount() == 2
    assert dialog._activity.item(0, 1).text() == "Ana Torres"
    assert dialog._activity.item(0, 2).text() == "Alta de usuario"
    assert dialog._activity.item(0, 3).text() == "Luis Paredes"
    assert dialog._activity.item(0, 4).text() == "Técnico"


def test_the_buttons_stay_disabled_until_a_row_is_chosen(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    dialog = UsersDialog(session_factory, admin)
    qtbot.addWidget(dialog)

    assert not dialog._edit_button.isEnabled()
    assert not dialog._password_button.isEnabled()
    assert not dialog._active_button.isEnabled()

    dialog._table.selectRow(0)

    assert dialog._edit_button.isEnabled()


def test_the_admin_cannot_deactivate_his_own_account(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    shown: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda _parent, _title, text: shown.append(text)
    )
    dialog = UsersDialog(session_factory, admin)
    qtbot.addWidget(dialog)
    dialog._table.selectRow(0)

    dialog._toggle_active()

    assert shown and "No puede desactivar" in shown[0]
    with session_factory() as session:
        assert get_user(session, "ana").activo is True


def test_deactivating_another_user_keeps_the_row_but_marks_it(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        create_user(session, username="luis", full_name="Luis Paredes", password=PASSWORD)
        session.commit()
    dialog = UsersDialog(session_factory, admin)
    qtbot.addWidget(dialog)
    dialog._table.selectRow(1)

    dialog._toggle_active()

    assert dialog._table.item(1, 3).text() == "Desactivado"
    assert dialog._active_button.text() == "Activar"
    with session_factory() as session:
        assert authenticate(session, "luis", PASSWORD) is None


def test_the_form_creates_a_user_with_its_password(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    dialog = UserFormDialog(session_factory)
    qtbot.addWidget(dialog)
    dialog._full_name.setText("Luis Paredes")
    dialog._username.setText("Luis")
    dialog._password.setText(PASSWORD)
    dialog._repeat.setText(PASSWORD)
    dialog._role.setCurrentIndex(dialog._role.findData(UserRole.TECNICO.value))

    dialog._save()

    assert dialog.result() == QDialog.DialogCode.Accepted
    with session_factory() as session:
        user = get_user(session, "luis")
        assert user is not None
        assert user.nombre_completo == "Luis Paredes"
        assert user.rol == UserRole.TECNICO.value


def test_the_form_does_not_change_the_username_of_an_existing_user(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    dialog = UserFormDialog(session_factory, admin.id)
    qtbot.addWidget(dialog)

    assert dialog._username.isReadOnly()
    assert dialog._username.text() == "ana"

    dialog._full_name.setText("Ana María Torres")
    dialog._save()

    with session_factory() as session:
        user = get_user(session, "ana")
        assert user is not None
        assert user.nombre_completo == "Ana María Torres"


def test_an_admin_can_reset_a_password(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    dialog = SetPasswordDialog(session_factory, admin.id)
    qtbot.addWidget(dialog)
    dialog._password.setText("nueva2026")
    dialog._repeat.setText("nueva2026")

    dialog._save()

    with session_factory() as session:
        assert authenticate(session, "ana", "nueva2026") is not None


def test_resetting_another_admin_password_asks_for_yours_and_records_it(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        jefe = create_user(
            session,
            username="jefe",
            full_name="Jefe de planta",
            password="jefe2026",
            role=UserRole.ADMINISTRADOR,
        )
        session.commit()
        jefe_id = jefe.id

    dialog = SetPasswordDialog(session_factory, jefe_id, actor=admin)
    qtbot.addWidget(dialog)
    assert dialog._needs_own_password is True
    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("bitácora" in text for text in texts)

    dialog._password.setText("nueva2026")
    dialog._repeat.setText("nueva2026")
    dialog._save()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "propia contraseña" in dialog._message.text()

    dialog._own_password.setText("no es")
    dialog._save()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "no es correcta" in dialog._message.text()

    dialog._own_password.setText(PASSWORD)
    dialog._save()

    assert dialog.result() == QDialog.DialogCode.Accepted
    with session_factory() as session:
        target = get_user(session, "jefe")
        assert target is not None
        assert target.debe_cambiar_contrasena is True
        assert authenticate(session, "jefe", "nueva2026") is not None
        event = list_user_events(session)[0]
        assert event.accion == UserAuditAction.CONTRASENA_RESTABLECIDA.value
        assert event.usuario_nombre == "Ana Torres"


def test_resetting_a_technician_password_does_not_ask_for_yours(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    with session_factory() as session:
        luis = create_user(
            session, username="luis", full_name="Luis Paredes", password=PASSWORD
        )
        session.commit()
        luis_id = luis.id

    dialog = SetPasswordDialog(session_factory, luis_id, actor=admin)
    qtbot.addWidget(dialog)

    assert dialog._needs_own_password is False
    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("bitácora" in text for text in texts)


def test_changing_your_own_password_needs_the_current_one(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    dialog = ChangePasswordDialog(session_factory, admin.id)
    qtbot.addWidget(dialog)
    dialog._current.setText("no es")
    dialog._new.setText("nueva2026")
    dialog._repeat.setText("nueva2026")

    dialog._save()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "actual no es correcta" in dialog._message.text()

    dialog._current.setText(PASSWORD)
    dialog._save()

    with session_factory() as session:
        assert authenticate(session, "ana", "nueva2026") is not None


# La sesión en la ventana principal


def _menu_titles(window: MainWindow) -> list[str]:
    menu = window.menuBar().actions()[0].menu()
    return [action.text() for action in menu.actions()]


def test_the_window_shows_who_is_logged_in(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)

    labels = [label.text() for label in window.statusBar().findChildren(QLabel)]
    assert window.user.display_name == "Ana Torres"
    assert any("Ana Torres" in text for text in labels)


def test_an_admin_sees_the_users_menu_and_a_technician_does_not(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    technician = CurrentUser(id=99, username="luis", full_name="Luis", role=UserRole.TECNICO.value)

    admin_window = MainWindow(session_factory, admin)
    qtbot.addWidget(admin_window)
    technician_window = MainWindow(session_factory, technician)
    qtbot.addWidget(technician_window)

    assert "&Usuarios…" in _menu_titles(admin_window)
    assert "&Usuarios…" not in _menu_titles(technician_window)
    assert "&Cerrar sesión" in _menu_titles(technician_window)


def test_logging_out_closes_the_window_and_asks_for_the_login_again(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)
    assert window.logout_requested is False

    window._logout()

    assert window.logout_requested is True


def test_the_orders_page_uses_the_name_of_the_session(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)

    assert window.orders_page._usuario == "Ana Torres"


# Bloqueo por inactividad


def test_the_unlock_dialog_only_accepts_the_password_of_the_session(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    admin = _seed(session_factory)
    dialog = UnlockDialog(session_factory, admin, INACTIVITY_LOCK_MINUTES)
    qtbot.addWidget(dialog)
    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("Ana Torres" in text for text in texts)

    dialog._password.setText("no es esta")
    dialog._unlock()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "incorrecta" in dialog._message.text()

    dialog._password.setText(PASSWORD)
    dialog._unlock()
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_the_window_locks_after_the_inactivity_period(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)
    assert window._lock_timer.isActive() is True
    locks: list[bool] = []
    monkeypatch.setattr(window, "_can_lock", lambda: True)
    monkeypatch.setattr(window, "_lock_session", lambda: locks.append(True))

    window._last_activity -= INACTIVITY_LOCK_MINUTES * 60 + 1
    window._check_inactivity()

    assert locks == [True]


def test_no_lock_happens_while_another_dialog_is_open(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)
    locks: list[bool] = []
    monkeypatch.setattr(window, "_can_lock", lambda: False)
    monkeypatch.setattr(window, "_lock_session", lambda: locks.append(True))

    window._last_activity -= INACTIVITY_LOCK_MINUTES * 60 + 1
    window._check_inactivity()

    assert locks == []


def test_the_fallback_session_without_an_account_never_locks(
    qtbot: QtBot, session_factory: sessionmaker[Session]
) -> None:
    window = MainWindow(session_factory)
    qtbot.addWidget(window)

    assert window._user.id is None
    assert window._lock_timer.isActive() is False


def test_a_dialog_open_past_the_limit_locks_when_it_closes(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)
    locks: list[bool] = []
    monkeypatch.setattr(window, "_lock_session", lambda: locks.append(True))

    dialog = QDialog(window)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    qtbot.addWidget(dialog)
    dialog.show()

    window._last_activity -= INACTIVITY_LOCK_MINUTES * 60 + 1
    window._check_inactivity()
    assert locks == []
    assert window._lock_pending is True

    dialog.close()
    qtbot.waitUntil(lambda: locks == [True], timeout=2000)


def test_a_dialog_opened_and_closed_before_the_limit_does_not_lock_nor_reset_the_countdown(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)
    locks: list[bool] = []
    monkeypatch.setattr(window, "_lock_session", lambda: locks.append(True))

    window._last_activity = monotonic() - 5 * 60
    remaining_before = monotonic() - window._last_activity

    dialog = QDialog(window)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    qtbot.addWidget(dialog)
    dialog.show()

    window._check_inactivity()
    assert window._lock_pending is False
    dialog.close()
    qtbot.wait(50)

    assert locks == []
    assert abs((monotonic() - window._last_activity) - remaining_before) < 2


def test_activity_inside_a_dialog_postpones_the_lock(
    qtbot: QtBot, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = _seed(session_factory)
    window = MainWindow(session_factory, admin)
    qtbot.addWidget(window)
    locks: list[bool] = []
    monkeypatch.setattr(window, "_lock_session", lambda: locks.append(True))

    dialog = QDialog(window)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    qtbot.addWidget(dialog)
    dialog.show()

    window._last_activity -= INACTIVITY_LOCK_MINUTES * 60 + 1
    window._check_inactivity()
    assert window._lock_pending is True

    qtbot.keyClick(dialog, Qt.Key.Key_A)
    assert window._lock_pending is False

    window._check_inactivity()
    assert locks == []


def test_the_users_of_the_database_survive_a_new_session(
    session_factory: sessionmaker[Session]
) -> None:
    _seed(session_factory)
    with session_factory() as session:
        assert [user.nombre_usuario for user in list_users(session)] == ["ana"]
