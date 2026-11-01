from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtCore import QEvent, Qt

from backend.controllers.settings_controller import SettingsController
from frontend.main_window import MainWindowCore
from frontend.window.window_state import WindowStateManager


def test_language_change_keeps_in_app_toast_without_system_notification(qapp):
    service = MagicMock()
    service.get_language.return_value = "en"
    toast = MagicMock()
    i18n = MagicMock()
    i18n.get.side_effect = lambda key: key
    controller = SettingsController(
        view=None,
        service=service,
        toast_manager=toast,
        i18n=i18n,
    )

    controller.handle_language_change("es")

    service.set_language.assert_called_once_with("es")
    toast.show_toast.assert_called_once_with(
        title="settings.status.lang_changed",
        message="settings.status.lang_changed_msg",
        state="info",
    )
    assert not hasattr(controller, "notification_requested")


def test_tray_tts_toggle_does_not_send_system_notification(qapp):
    window = SimpleNamespace(
        chat_controller=MagicMock(),
        tray_manager=MagicMock(),
    )

    MainWindowCore._handle_tray_tts_toggle(window, True)

    window.chat_controller.set_tts_option.assert_called_once_with("enabled", True)
    window.tray_manager.showMessage.assert_not_called()


def test_minimizing_to_tray_hides_window_without_notification(qapp):
    window = MagicMock()
    window.isMinimized.return_value = True
    config = MagicMock()
    config.load_bool.return_value = True
    event = MagicMock()
    event.type.return_value = QEvent.Type.WindowStateChange
    event.oldState.return_value = Qt.WindowState.WindowMaximized
    manager = WindowStateManager(window, config)

    manager.handle_state_change(event)

    window.hide.assert_called_once_with()
    assert not hasattr(manager, "_on_hidden_to_tray")
