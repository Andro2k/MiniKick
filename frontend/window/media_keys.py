# frontend\window\media_keys.py

import logging
import sys
from typing import Callable

from PySide6.QtCore import Qt, QThread

from backend.connections import WorkerSlot
from backend.interfaces import IConfigProvider

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
    SETTING_GLOBAL_KEYS = "music_global_media_keys"

    def __init__(
        self,
        music_controller,
        config: IConfigProvider,
        slot: WorkerSlot,
        worker_factory: Callable[[], QThread],
        is_shutting_down: Callable[[], bool],
    ) -> None:
        self._music_controller = music_controller
        self._config = config
        self._worker_factory = worker_factory
        self._is_shutting_down = is_shutting_down
        self.slot = slot
        self._global_keys_enabled = False
        self._start_pending = False

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

    def setup_global_keys(self) -> None:
        if sys.platform != "win32":
            return
        self._global_keys_enabled = self._config.load_bool(self.SETTING_GLOBAL_KEYS, True)
        if self._global_keys_enabled:
            self._start_global_worker()
        self._music_controller.media_keys_state_changed.connect(self._on_global_keys_changed)

    def _on_global_keys_changed(self, enabled: bool) -> None:
        self._global_keys_enabled = enabled
        if enabled:
            self._start_global_worker()
        else:
            self.slot.stop()

    def _start_global_worker(self) -> None:
        self._global_keys_enabled = True
        if self.slot.is_running or self._start_pending or self._is_shutting_down():
            return
        self._start_pending = True
        self.slot.stop(on_finished=self._create_global_worker)

    def _create_global_worker(self) -> None:
        self._start_pending = False
        if self._is_shutting_down() or not self._global_keys_enabled:
            return
        self.slot.start(self._build_global_worker)

    def _build_global_worker(self) -> QThread:
        worker = self._worker_factory()
        worker.play_pause_pressed.connect(self._music_controller.handle_play_pause)
        worker.skip_pressed.connect(self._music_controller.handle_skip)
        worker.stop_pressed.connect(self._music_controller.handle_play_pause)
        return worker
