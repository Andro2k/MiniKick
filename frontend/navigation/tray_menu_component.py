# frontend\navigation\tray_menu_component.py

import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal
from frontend.common import (
    resource_path, get_icon_colored,
    COLOR_WHITE, COLOR_RED
)

class SystemTrayManager(QSystemTrayIcon):
    restore_requested = Signal()
    quit_requested = Signal()
    tts_toggled = Signal(bool)
    play_pause_requested = Signal()
    skip_requested = Signal()
    tts_use_command_toggled = Signal(bool)
    tts_voice_type_changed = Signal(bool)

    def __init__(self, i18n, parent=None):
        self.i18n = i18n
        self._is_playing = False
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        self.setIcon(QIcon(icon_path))
        tooltip_template = self.i18n.get("main.tray.tooltip")
        self.setToolTip(tooltip_template.replace("{version}", "1.6.0") if "{version}" in tooltip_template else tooltip_template)

        self.menu = QMenu(self.parent())

        self.action_restore = self.menu.addAction(
            get_icon_colored("squares-filled.svg", COLOR_WHITE, 16),
            self.i18n.get("main.tray.open_panel")
        )
        self.action_restore.triggered.connect(self.restore_requested.emit)

        self.menu.addSeparator()

        self.action_play_pause = self.menu.addAction(
            get_icon_colored("play-filled.svg", COLOR_WHITE, 16),
            self.i18n.get("main.tray.play")
        )
        self.action_play_pause.triggered.connect(self.play_pause_requested.emit)

        self.action_skip = self.menu.addAction(
            get_icon_colored("skip-next-filled.svg", COLOR_WHITE, 16),
            self.i18n.get("main.tray.skip")
        )
        self.action_skip.triggered.connect(self.skip_requested.emit)

        self.menu.addSeparator()

        self.action_tts = QAction(
            get_icon_colored("voice-cricle-filled.svg", COLOR_WHITE, 16),
            self.i18n.get("main.tray.read_chat"),
            self.menu
        )
        self.action_tts.setCheckable(True)
        self.action_tts.toggled.connect(self.tts_toggled.emit)
        self.menu.addAction(self.action_tts)

        self.action_tts_use_command = QAction(
            get_icon_colored("hashtag-filled.svg", COLOR_WHITE, 16),
            self.i18n.get("main.tray.tts_use_command"),
            self.menu
        )
        self.action_tts_use_command.setCheckable(True)
        self.action_tts_use_command.toggled.connect(self.tts_use_command_toggled.emit)
        self.menu.addAction(self.action_tts_use_command)

        self.action_tts_voice_type = QAction(
            get_icon_colored("globe-filled.svg", COLOR_WHITE, 16),
            self.i18n.get("main.tray.tts_voice_type"),
            self.menu
        )
        self.action_tts_voice_type.setCheckable(True)
        self.action_tts_voice_type.toggled.connect(self.tts_voice_type_changed.emit)
        self.menu.addAction(self.action_tts_voice_type)

        self.menu.addSeparator()

        self.action_quit = self.menu.addAction(
            get_icon_colored("x-filled.svg", COLOR_RED, 16),
            self.i18n.get("main.tray.close_app")
        )
        self.action_quit.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_requested.emit()

    def set_playback_state(self, is_playing: bool):
        self._is_playing = is_playing
        if is_playing:
            self.action_play_pause.setText(self.i18n.get("main.tray.pause"))
            self.action_play_pause.setIcon(get_icon_colored("pause-filled.svg", COLOR_WHITE, 16))
        else:
            self.action_play_pause.setText(self.i18n.get("main.tray.play"))
            self.action_play_pause.setIcon(get_icon_colored("play-filled.svg", COLOR_WHITE, 16))

    def set_tts_state(self, enabled: bool):
        self.action_tts.blockSignals(True)
        self.action_tts.setChecked(enabled)
        self.action_tts.blockSignals(False)

    def set_tts_use_command_state(self, enabled: bool):
        self.action_tts_use_command.blockSignals(True)
        self.action_tts_use_command.setChecked(enabled)
        self.action_tts_use_command.blockSignals(False)

    def set_tts_voice_type_state(self, is_web: bool):
        self.action_tts_voice_type.blockSignals(True)
        self.action_tts_voice_type.setChecked(is_web)
        self.action_tts_voice_type.blockSignals(False)
