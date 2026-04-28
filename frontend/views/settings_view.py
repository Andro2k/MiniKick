# frontend/views/settings_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, Signal

from frontend.components.switch import IconSwitch

class SettingsView(QWidget):
    # --- NUEVO NOMBRE DE SEÑAL ---
    minimize_tray_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(20)

        title = QLabel("Configuración General")
        title.setProperty("role", "title")
        layout.addWidget(title)

        sys_card = QFrame()
        sys_card.setObjectName("Card")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(15)

        sys_title = QLabel("COMPORTAMIENTO DE VENTANA")
        sys_title.setProperty("role", "section")
        sys_layout.addWidget(sys_title)

        start_bg_layout = QHBoxLayout()
        # --- NUEVO TEXTO ---
        lbl_start_bg = QLabel("Minimizar a la bandeja del sistema")
        
        self.sw_start_bg = IconSwitch(icon_on="monitor.svg", icon_off="minimize-2.svg")
        self.sw_start_bg.setCursor(Qt.CursorShape.PointingHandCursor)
        # --- ENLACE A NUEVA SEÑAL ---
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)
        
        start_bg_layout.addWidget(lbl_start_bg)
        start_bg_layout.addStretch() 
        start_bg_layout.addWidget(self.sw_start_bg)
        
        sys_layout.addLayout(start_bg_layout)
        layout.addWidget(sys_card)
        layout.addStretch()

    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.setChecked(enabled)