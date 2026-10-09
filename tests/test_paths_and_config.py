"""Pruebas del paso 1: configuración central y rutas XDG."""

from __future__ import annotations

from pathlib import Path

from luciotech import APP_VERSION
from luciotech.config import APP_CONFIG
from luciotech.utils import paths


def test_app_identity_is_centralized() -> None:
    assert APP_CONFIG.app_name == "LucioTech Service Manager"
    assert APP_CONFIG.app_id == "luciotech-service-manager"
    assert APP_CONFIG.organization_name == "Ing. Lucio"
    assert APP_VERSION == APP_CONFIG.application_version


def test_data_dir_uses_xdg_data_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "_is_windows", lambda: False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert paths.data_dir() == tmp_path / APP_CONFIG.app_id
    assert paths.database_path() == tmp_path / APP_CONFIG.app_id / "database.sqlite3"


def test_state_dir_uses_xdg_state_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "_is_windows", lambda: False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert paths.log_dir() == tmp_path / APP_CONFIG.app_id / "logs"


def test_default_data_dir_falls_back_to_home_local_share(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "_is_windows", lambda: False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert paths.data_dir() == tmp_path / ".local" / "share" / APP_CONFIG.app_id
