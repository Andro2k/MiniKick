# frontend/components/tray_menu.py

import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal

from frontend.common.utils import resource_path

class SystemTrayManager(QSystemTrayIcon):
    restore_requested = Signal()
    quit_requested = Signal()
    tts_toggled = Signal(bool)

    def __init__(self, i18n, parent=None):
        self.i18n = i18n
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        self.setIcon(QIcon(icon_path))

        self.menu = QMenu()

        self.action_restore = self.menu.addAction(self.i18n.get("main.tray.open_panel"))
        self.action_restore.triggered.connect(self.restore_requested.emit)

        self.menu.addSeparator()

        self.action_tts = QAction(self.i18n.get("main.tray.read_chat"), self.menu)
        self.action_tts.setCheckable(True)
        self.action_tts.toggled.connect(self.tts_toggled.emit)
        self.menu.addAction(self.action_tts)

        self.menu.addSeparator()

        self.action_quit = self.menu.addAction(self.i18n.get("main.tray.close_app"))
        self.action_quit.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_requested.emit()

    def set_tts_state(self, enabled: bool):
        self.action_tts.blockSignals(True)
        self.action_tts.setChecked(enabled)
        self.action_tts.blockSignals(False)