# frontend\window\media_keys.py

import logging
import sys

from PySide6.QtCore import Qt

logger = logging.getLogger("minikick.core")

_PLAY_PAUSE = "handle_play_pause"
_SKIP = "handle_skip"

_WM_APPCOMMAND = 0x0319
_NATIVE_APPCOMMANDS = {
    11: _SKIP,
    13: _PLAY_PAUSE,
    14: _PLAY_PAUSE,
    46: _PLAY_PAUSE,
    47: _PLAY_PAUSE,
}
_QT_MEDIA_KEYS = {
    Qt.Key.Key_MediaTogglePlayPause: _PLAY_PAUSE,
    Qt.Key.Key_MediaPlay: _PLAY_PAUSE,
    Qt.Key.Key_MediaPause: _PLAY_PAUSE,
    Qt.Key.Key_Play: _PLAY_PAUSE,
    Qt.Key.Key_Pause: _PLAY_PAUSE,
    Qt.Key.Key_MediaStop: _PLAY_PAUSE,
    Qt.Key.Key_MediaNext: _SKIP,
}
_WINDOWS_MSG_EVENT_TYPES = (b"windows_generic_MSG", "windows_generic_MSG")


class MediaKeysHandler:
    def __init__(self, music_controller) -> None:
        self._music_controller = music_controller

    def handle_key(self, key: int) -> bool:
        action = _QT_MEDIA_KEYS.get(key)
        if action is None:
            return False
        getattr(self._music_controller, action)()
        return True

    def handle_native_event(self, event_type, message) -> bool:
        if sys.platform != "win32" or event_type not in _WINDOWS_MSG_EVENT_TYPES:
            return False
        try:
            from ctypes import wintypes
            msg = wintypes.MSG.from_address(int(message))
            if msg.message != _WM_APPCOMMAND:
                return False
            app_cmd = (msg.lParam >> 16) & ~0xF000
            action = _NATIVE_APPCOMMANDS.get(app_cmd)
            if action is None:
                return False
            getattr(self._music_controller, action)()
            return True
        except (OSError, OverflowError, TypeError, ValueError) as error:
            logger.warning(
                "[MediaKeys] Failed to process native media-key event: %s",
                error,
                exc_info=True,
            )
            return False
