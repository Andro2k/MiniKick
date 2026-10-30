# resources\tests\test_chat_detached_window.py

from types import SimpleNamespace

from PySide6.QtWidgets import QMainWindow, QSizeGrip
from PySide6.QtCore import Qt
from shiboken6 import isValid

from backend.services.system import TranslationService
from frontend.main_window import MainWindowCore
from frontend.views.chat_view import ChatView, _FloatingChatWindow


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


def test_close_floating_chat_without_window_is_a_noop(qapp):
    view = ChatView(TranslationService(default_lang="es"))
    view.close_floating_chat()
    assert view._floating_chat_dialog is None


def test_app_shutdown_closes_the_floating_chat(qapp):
    host, view, floating = _detached_chat(qapp)
    fake_window = SimpleNamespace(
        _is_shutting_down=False,
        _is_window_closing=False,
        _dashboard_metrics_timer=SimpleNamespace(stop=lambda: None),
        view_chat=view,
        logger=SimpleNamespace(info=lambda *a, **k: None),
        _stop_all_workers=lambda callback: None,
        _finish_cleanup=lambda: None,
    )

    MainWindowCore._cleanup(fake_window)
    qapp.processEvents()

    assert view._floating_chat_dialog is None
    assert not isValid(floating) or not floating.isVisible()
    host.close()
