# frontend/components/tray_menu.py

import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal

from frontend.utils import resource_path

class SystemTrayManager(QSystemTrayIcon):
    # ─── CONTRATOS DE SALIDA (Hacia MainWindow) ───
    restore_requested = Signal()
    quit_requested = Signal()
    tts_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        self.setIcon(QIcon(icon_path))

        self.menu = QMenu()

        # Acción: Restaurar
        self.action_restore = self.menu.addAction("Abrir Panel")
        self.action_restore.triggered.connect(self.restore_requested.emit)

        self.menu.addSeparator()

        # Acción: Toggle TTS (Con Checkbox)
        self.action_tts = QAction("Leer chat en voz alta", self.menu)
        self.action_tts.setCheckable(True)
        self.action_tts.toggled.connect(self.tts_toggled.emit)
        self.menu.addAction(self.action_tts)

        self.menu.addSeparator()

        # Acción: Salir
        self.action_quit = self.menu.addAction("Cerrar MiniKick")
        self.action_quit.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        # Si hacen doble clic en el ícono, abre la app
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_requested.emit()

    # ─── CONTRATOS DE ESTADO (Desde MainWindow) ───
    def set_tts_state(self, enabled: bool):
        """Sincroniza visualmente el checkbox del menú con el estado real de la base de datos."""
        self.action_tts.blockSignals(True)
        self.action_tts.setChecked(enabled)
        self.action_tts.blockSignals(False)