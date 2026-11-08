# resources\tests\test_chat_detached_window.py

from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtWidgets import QMainWindow, QSizeGrip
from PySide6.QtCore import Qt
from shiboken6 import isValid

from backend.config.toml_config_provider import TomlConfigProvider
from backend.services.system import TranslationService
from frontend.window.shutdown import MainWindowShutdown
from frontend.views.chat_view import ChatView, SETTING_FLOATING_CHAT_GEOMETRY, _FloatingChatWindow


def test_floating_chat_window_exposes_windows_snap_controls(qapp):
    window = _FloatingChatWindow("Chat", lambda: None)
    flags = window.windowFlags()

    assert flags & Qt.WindowType.WindowMaximizeButtonHint
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowSystemMenuHint

    window.close()


def test_floating_chat_window_can_be_resized(qapp):
    window = _FloatingChatWindow("Chat", lambda: None)
    window.show()
    qapp.processEvents()

    resize_grip = window.findChild(QSizeGrip)
    assert resize_grip is not None
    assert resize_grip.isVisible()

    initial_size = window.size()
    window.resize(initial_size.width() + 50, initial_size.height() + 50)
    qapp.processEvents()

    assert window.size() != initial_size
    window.close()


def _detached_chat(qapp):
    host = QMainWindow()
    view = ChatView(TranslationService(default_lang="es"))
    host.setCentralWidget(view)
    host.show()
    view._detach_chat_display()
    qapp.processEvents()
    return host, view, view._floating_chat_dialog


def test_floating_chat_window_is_a_real_top_level_window(qapp):
    window = _FloatingChatWindow("Chat", lambda: None)

    assert window.parent() is None
    assert window.isWindow()
    window.close()


def test_detached_chat_has_no_owner_so_it_ignores_main_window_minimize(qapp):
    host, view, floating = _detached_chat(qapp)

    assert floating is not None and floating.isVisible()
    assert floating.parentWidget() is None
    assert floating.windowHandle().transientParent() is None
    assert host.windowHandle() is not floating.windowHandle()

    view.close_floating_chat()
    host.close()


def test_minimizing_floating_chat_does_not_redock_it(qapp):
    returned = []
    window = _FloatingChatWindow("Chat", lambda: returned.append(True))
    window.show()
    qapp.processEvents()

    window.setWindowState(Qt.WindowState.WindowMinimized)
    qapp.processEvents()

    assert window.isMinimized()
    assert returned == []
    window.close()


def test_close_floating_chat_returns_panel_to_main_view(qapp):
    host, view, floating = _detached_chat(qapp)
    assert view.chat_display_panel.window() is floating

    view.close_floating_chat()
    qapp.processEvents()

    assert view._floating_chat_dialog is None
    assert view.chat_display_panel.window() is host
    host.close()


def test_redetaching_chat_restores_last_floating_position_and_size(qapp):
    host, view, floating = _detached_chat(qapp)
    floating.resize(720, 640)
    floating.move(80, 90)
    qapp.processEvents()
    expected_geometry = floating.geometry()

    view._reattach_chat_display()
    qapp.processEvents()
    view._detach_chat_display()
    qapp.processEvents()

    restored = view._floating_chat_dialog
    assert restored is not None
    actual_geometry = restored.geometry()
    assert abs(actual_geometry.x() - expected_geometry.x()) <= 5
    assert abs(actual_geometry.y() - expected_geometry.y()) <= 5
    assert (actual_geometry.width(), actual_geometry.height()) == (
        expected_geometry.width(), expected_geometry.height()
    )

    view.close_floating_chat()
    host.close()


def test_floating_chat_geometry_persists_across_chat_view_instances(qapp, tmp_path):
    config_path = tmp_path / "config.toml"
    config = TomlConfigProvider(config_path)
    first_host = QMainWindow()
    first_view = ChatView(TranslationService(default_lang="es"), config=config)
    first_host.setCentralWidget(first_view)
    first_host.show()
    first_view._detach_chat_display()
    qapp.processEvents()

    floating = first_view._floating_chat_dialog
    floating.resize(560, 500)
    floating.move(20, 20)
    qapp.processEvents()
    expected_geometry = floating.geometry()
    first_view.close_floating_chat()
    qapp.processEvents()

    saved_geometry = config.load_string(SETTING_FLOATING_CHAT_GEOMETRY, "")
    assert saved_geometry
    config = TomlConfigProvider(config_path)

    second_host = QMainWindow()
    second_view = ChatView(TranslationService(default_lang="es"), config=config)
    second_host.setCentralWidget(second_view)
    second_host.show()
    second_view._detach_chat_display()
    qapp.processEvents()

    restored_geometry = second_view._floating_chat_dialog.geometry()
    assert abs(restored_geometry.x() - expected_geometry.x()) <= 5
    assert abs(restored_geometry.y() - expected_geometry.y()) <= 5
    assert (restored_geometry.width(), restored_geometry.height()) == (
        expected_geometry.width(), expected_geometry.height()
    )

    second_view.close_floating_chat()
    first_host.close()
    second_host.close()


def test_close_floating_chat_without_window_is_a_noop(qapp):
    view = ChatView(TranslationService(default_lang="es"))
    view.close_floating_chat()
    assert view._floating_chat_dialog is None


def test_app_shutdown_closes_the_floating_chat(qapp):
    host, view, floating = _detached_chat(qapp)
    fake_window = SimpleNamespace(
        _is_shutting_down=False,
        session_metrics=SimpleNamespace(stop=lambda: None),
        view_chat=view,
    )
    shutdown = MainWindowShutdown.__new__(MainWindowShutdown)
    shutdown._window = fake_window
    shutdown._sequence = SimpleNamespace(run=MagicMock())

    shutdown.cleanup()
    qapp.processEvents()

    shutdown._sequence.run.assert_called_once_with()

    assert view._floating_chat_dialog is None
    assert not isValid(floating) or not floating.isVisible()
    host.close()
