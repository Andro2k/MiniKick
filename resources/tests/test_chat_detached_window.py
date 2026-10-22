from PySide6.QtWidgets import QSizeGrip
from PySide6.QtCore import Qt

from frontend.views.chat_view import _FloatingChatWindow


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
