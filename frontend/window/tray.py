# frontend\window\tray.py

from __future__ import annotations

from PySide6.QtCore import Slot

from frontend.navigation import SystemTrayManager


class TrayPresenter:
    def __init__(self, window) -> None:
        self._window = window

    def setup(self) -> None:
        w = self._window
        w.tray_manager = SystemTrayManager(w.i18n, w)
        w.tray_manager.restore_requested.connect(w.window_state.restore_from_tray)
        w.tray_manager.quit_requested.connect(w._force_quit)
        w.tray_manager.tts_toggled.connect(self.handle_tts_toggle)
        w.tray_manager.play_pause_requested.connect(self.handle_play_pause)
        w.tray_manager.skip_requested.connect(self.handle_skip)
        w.tray_manager.tts_use_command_toggled.connect(self.handle_tts_use_command_toggle)
        w.tray_manager.tts_voice_type_changed.connect(self.handle_tts_voice_type_change)
        w.tray_manager.show()

    @Slot(bool)
    def handle_tts_toggle(self, enabled: bool) -> None:
        self._window.chat_controller.set_tts_option("enabled", enabled)

    @Slot()
    def handle_play_pause(self) -> None:
        self._window.music_controller.handle_play_pause()

    @Slot()
    def handle_skip(self) -> None:
        self._window.music_controller.handle_skip()

    @Slot(object)
    def handle_song_changed(self, song: dict) -> None:
        is_playing = bool(song.get("is_playing", False)) if isinstance(song, dict) else False
        self._window.tray_manager.set_playback_state(is_playing)

    @Slot(bool)
    def handle_tts_use_command_toggle(self, enabled: bool) -> None:
        self._window.chat_controller.set_tts_option("use_command", enabled)

    @Slot(bool)
    def handle_tts_voice_type_change(self, is_web: bool) -> None:
        self._window.chat_controller.set_tts_option(
            "provider",
            "web" if is_web else "piper",
        )

    @Slot(bool)
    def handle_chat_tts_state_changed(self, enabled: bool) -> None:
        w = self._window
        settings = w.chat_service.get_settings()
        w.tray_manager.set_tts_state(enabled)
        w.tray_manager.set_tts_use_command_state(settings.get("use_command", False))
        w.tray_manager.set_tts_voice_type_state(settings.get("provider", "piper") == "web")
