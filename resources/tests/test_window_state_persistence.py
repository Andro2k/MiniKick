# resources\tests\test_window_state_persistence.py

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QByteArray
from pathlib import Path
import sys
from PySide6.QtCore import QEventLoop, QTimer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.main_window import MainWindowCore

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

class MockSettingsStorage:
    def __init__(self):
        self._data = {}

    def load_bool(self, key, default=False):
        return self._data.get(key, default)

    def save_bool(self, key, value):
        self._data[key] = value

    def load_string(self, key, default=""):
        return self._data.get(key, default)

    def save_string(self, key, value):
        self._data[key] = value

@pytest.fixture
def managed_window(qapp):
    windows = []

    def _create():
        updater = MagicMock()
        win = MainWindowCore(updater_manager=updater, app_version="1.6.1")
        windows.append(win)
        return win

    yield _create

    for win in windows:
        win._cleanup()
        if not win._cleanup_complete:
            event_loop = QEventLoop()
            timeout = QTimer()
            timeout.setSingleShot(True)
            timeout.timeout.connect(event_loop.quit)
            win.shutdown_finished.connect(event_loop.quit)
            timeout.start(5000)
            event_loop.exec()
            timeout.stop()
            win.shutdown_finished.disconnect(event_loop.quit)
        assert win._cleanup_complete
        win.deleteLater()

def test_window_state_default_maximized(qapp, managed_window, monkeypatch):
    window = managed_window()
    window.settings_storage = MockSettingsStorage()

    show_max_called = []
    monkeypatch.setattr(window, "showMaximized", lambda: show_max_called.append(True))
    monkeypatch.setattr(window, "show", lambda: None)

    window.restore_window_state()

    assert show_max_called == [True]
    assert window._was_maximized_before_tray is True

def test_window_state_normal_geometry_restored(qapp, managed_window, monkeypatch):
    window = managed_window()
    storage = MockSettingsStorage()
    storage.save_bool(MainWindowCore.SETTING_WINDOW_MAXIMIZED, False)
    dummy_geom = bytes(QByteArray(b"\x01\x02\x03\x04")).hex()
    storage.save_string(MainWindowCore.SETTING_WINDOW_GEOMETRY, dummy_geom)
    window.settings_storage = storage

    show_normal_called = []
    restore_geom_called = []
    monkeypatch.setattr(window, "showMaximized", lambda: None)
    monkeypatch.setattr(window, "show", lambda: show_normal_called.append(True))
    monkeypatch.setattr(window, "restoreGeometry", lambda g: restore_geom_called.append(g))

    window.restore_window_state()

    assert show_normal_called == [True]
    assert len(restore_geom_called) == 1
    assert window._was_maximized_before_tray is False

def test_save_window_state_when_maximized(qapp, managed_window, monkeypatch):
    window = managed_window()
    storage = MockSettingsStorage()
    window.settings_storage = storage

    monkeypatch.setattr(window, "isMinimized", lambda: False)
    monkeypatch.setattr(window, "isMaximized", lambda: True)

    window._save_window_state()

    assert storage.load_bool(MainWindowCore.SETTING_WINDOW_MAXIMIZED, False) is True

def test_save_window_state_when_normal(qapp, managed_window, monkeypatch):
    window = managed_window()
    storage = MockSettingsStorage()
    window.settings_storage = storage

    monkeypatch.setattr(window, "isMinimized", lambda: False)
    monkeypatch.setattr(window, "isMaximized", lambda: False)
    monkeypatch.setattr(window, "saveGeometry", lambda: QByteArray(b"geom_bytes"))

    window._save_window_state()

    assert storage.load_bool(MainWindowCore.SETTING_WINDOW_MAXIMIZED, True) is False
    assert storage.load_string(MainWindowCore.SETTING_WINDOW_GEOMETRY, "") == bytes(QByteArray(b"geom_bytes")).hex()

def test_restore_from_tray_preserves_maximized(qapp, managed_window, monkeypatch):
    window = managed_window()
    window._was_maximized_before_tray = True

    show_max_called = []
    monkeypatch.setattr(window, "showMaximized", lambda: show_max_called.append(True))
    monkeypatch.setattr(window, "showNormal", lambda: None)
    monkeypatch.setattr(window, "activateWindow", lambda: None)

    window._restore_from_tray()

    assert show_max_called == [True]
