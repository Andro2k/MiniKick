from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtWidgets import QDialog

from backend.services.system.settings_service import SettingsService
from frontend.main_window import MainWindowCore
from frontend.views.settings_view import SettingsView
from backend.services.system import TranslationService


class _SettingsStorage:
    def __init__(self):
        self.values = {}

    def load_bool(self, key, default=False):
        return self.values.get(key, default)

    def save_bool(self, key, value):
        self.values[key] = value


def test_auto_update_preference_defaults_off_and_persists():
    storage = _SettingsStorage()
    service = SettingsService(storage, backup_service=None)

    assert service.is_auto_update_download_enabled() is False

    service.set_auto_update_download_enabled(True)

    assert storage.values[service.SETTING_AUTO_UPDATE_DOWNLOAD] is True
    assert service.is_auto_update_download_enabled() is True


def test_settings_view_auto_update_switch_emits_and_restores_state(qapp):
    view = SettingsView(i18n=TranslationService(default_lang="es"))
    changed = []
    view.auto_update_download_toggled.connect(changed.append)

    view.set_auto_update_download_enabled(True)
    assert view.sw_auto_update_download.isChecked() is True
    assert changed == []

    view.sw_auto_update_download.setChecked(False)
    assert changed == [False]


def _auto_update_window(enabled=True):
    window = SimpleNamespace(
        settings_service=SimpleNamespace(
            is_auto_update_download_enabled=lambda: enabled
        ),
        updater_controller=SimpleNamespace(
            download_worker=None,
            start_download=MagicMock(return_value=True),
            install_update=MagicMock(),
        ),
        sidebar=SimpleNamespace(set_update_available=MagicMock()),
        toast=SimpleNamespace(show_toast=MagicMock()),
        i18n=TranslationService(default_lang="es"),
        logger=MagicMock(),
        _is_worker_running=MainWindowCore._is_worker_running,
        _is_shutting_down=False,
        _auto_update_download_active=False,
        _auto_update_info={},
        _force_quit=MagicMock(),
    )
    window._download_update_if_enabled = lambda info: (
        MainWindowCore._download_update_if_enabled(window, info)
    )
    return window


def test_silent_update_starts_download_only_when_preference_enabled():
    window = _auto_update_window()
    update_info = {
        "version": "2.0.0",
        "download_url": "https://example.invalid/update.exe",
    }

    MainWindowCore._on_silent_update_found(window, update_info)

    window.updater_controller.start_download.assert_called_once_with(
        update_info["download_url"]
    )
    assert window._auto_update_download_active is True

    manual_window = _auto_update_window(enabled=False)
    MainWindowCore._on_silent_update_found(manual_window, update_info)
    manual_window.updater_controller.start_download.assert_not_called()


def test_auto_download_completion_requires_install_confirmation(monkeypatch):
    import frontend.main_window as main_window_module

    window = _auto_update_window()
    window._auto_update_download_active = True
    window._auto_update_info = {"version": "2.0.0"}
    dialog = MagicMock()
    dialog.DialogCode = QDialog.DialogCode
    dialog.exec.return_value = QDialog.DialogCode.Rejected
    monkeypatch.setattr(
        main_window_module,
        "ModernConfirmDialog",
        MagicMock(return_value=dialog),
    )

    MainWindowCore._on_auto_update_download_finished(window, True)

    window.updater_controller.install_update.assert_not_called()
    window._force_quit.assert_not_called()
    window.toast.show_toast.assert_called_once()


def test_auto_download_completion_can_install_when_confirmed(monkeypatch):
    import frontend.main_window as main_window_module

    window = _auto_update_window()
    window._auto_update_download_active = True
    window._auto_update_info = {"version": "2.0.0"}
    dialog = MagicMock()
    dialog.DialogCode = QDialog.DialogCode
    dialog.exec.return_value = QDialog.DialogCode.Accepted
    monkeypatch.setattr(
        main_window_module,
        "ModernConfirmDialog",
        MagicMock(return_value=dialog),
    )

    MainWindowCore._on_auto_update_download_finished(window, True)

    window.updater_controller.install_update.assert_called_once_with()
    window._force_quit.assert_called_once_with()
