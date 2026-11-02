from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtWidgets import QDialog, QWidget

from backend.services.system.settings_service import SettingsService
from frontend.window.updates import AutoUpdateCoordinator
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


def _auto_update_coordinator(enabled=True):
    updater = SimpleNamespace(
        download_worker=None,
        start_download=MagicMock(return_value=True),
        install_update=MagicMock(),
    )
    sidebar = SimpleNamespace(set_update_available=MagicMock())
    toast = SimpleNamespace(show_toast=MagicMock())
    request_quit = MagicMock()
    coordinator = AutoUpdateCoordinator(
        parent=QWidget(),
        updater_controller=updater,
        settings_service=SimpleNamespace(is_auto_update_download_enabled=lambda: enabled),
        sidebar=sidebar,
        toast=toast,
        i18n=TranslationService(default_lang="es"),
        is_shutting_down=lambda: False,
        request_quit=request_quit,
    )
    return coordinator, updater, toast, request_quit


def test_silent_update_starts_download_only_when_preference_enabled(qapp):
    coordinator, updater, _toast, _quit = _auto_update_coordinator()
    update_info = {
        "version": "2.0.0",
        "download_url": "https://example.invalid/update.exe",
    }

    coordinator.on_update_found(update_info)

    updater.start_download.assert_called_once_with(update_info["download_url"])
    assert coordinator.download_active is True

    manual, manual_updater, _toast, _quit = _auto_update_coordinator(enabled=False)
    manual.on_update_found(update_info)
    manual_updater.start_download.assert_not_called()


def _confirm_dialog(monkeypatch, result):
    import frontend.window.updates as updates_module

    dialog = MagicMock()
    dialog.DialogCode = QDialog.DialogCode
    dialog.exec.return_value = result
    monkeypatch.setattr(updates_module, "ModernConfirmDialog", MagicMock(return_value=dialog))


def test_auto_download_completion_requires_install_confirmation(qapp, monkeypatch):
    coordinator, updater, toast, request_quit = _auto_update_coordinator()
    coordinator.download_active = True
    coordinator._info = {"version": "2.0.0"}
    _confirm_dialog(monkeypatch, QDialog.DialogCode.Rejected)

    coordinator.on_download_finished(True)

    updater.install_update.assert_not_called()
    request_quit.assert_not_called()
    toast.show_toast.assert_called_once()


def test_auto_download_completion_can_install_when_confirmed(qapp, monkeypatch):
    coordinator, updater, _toast, request_quit = _auto_update_coordinator()
    coordinator.download_active = True
    coordinator._info = {"version": "2.0.0"}
    _confirm_dialog(monkeypatch, QDialog.DialogCode.Accepted)

    coordinator.on_download_finished(True)

    updater.install_update.assert_called_once_with()
    request_quit.assert_called_once_with()
