# frontend/views/settings_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

from frontend.components.button import ModernButton
from frontend.components.switch import ModernSwitch

class SettingsView(QWidget):
    minimize_tray_toggled = Signal(bool)
    unlink_account_requested = Signal()
    check_update_requested = Signal() 

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        title = QLabel("Configuración General")
        title.setProperty("role", "title")
        layout.addWidget(title)

        # --- Tarjeta 1: Comportamiento de Ventana ---
        sys_card = QFrame()
        sys_card.setObjectName("Card")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(15)

        sys_title = QLabel("COMPORTAMIENTO DE VENTANA")
        sys_title.setProperty("role", "section")
        sys_layout.addWidget(sys_title)

        start_bg_layout = QHBoxLayout()
        lbl_start_bg = QLabel("Minimizar a la bandeja del sistema")
        
        self.sw_start_bg = ModernSwitch()
        self.sw_start_bg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)
        
        start_bg_layout.addWidget(lbl_start_bg)
        start_bg_layout.addStretch() 
        start_bg_layout.addWidget(self.sw_start_bg)
        
        sys_layout.addLayout(start_bg_layout)
        layout.addWidget(sys_card)

        # --- Tarjeta 2: Gestión de Cuenta ---
        account_card = QFrame()
        account_card.setObjectName("Card")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(20, 20, 20, 20)
        account_layout.setSpacing(15)

        account_title = QLabel("GESTIÓN DE CUENTA")
        account_title.setProperty("role", "section")
        account_layout.addWidget(account_title)

        unlink_layout = QHBoxLayout()
        lbl_unlink = QLabel("Desvincular cuenta de Kick (Cierra la sesión actual)")
        lbl_unlink.setProperty("role", "subtitle")
        
        # 2. Uso del ModernButton (Variante Peligro)
        self.btn_unlink = ModernButton("Desvincular", role="action_danger")
        self.btn_unlink.clicked.connect(self.unlink_account_requested.emit)

        unlink_layout.addWidget(lbl_unlink)
        unlink_layout.addStretch()
        unlink_layout.addWidget(self.btn_unlink)

        account_layout.addLayout(unlink_layout)
        layout.addWidget(account_card)

        # --- NUEVA Tarjeta 3: Sistema y Actualizaciones ---
        update_card = QFrame()
        update_card.setObjectName("Card")
        update_layout = QVBoxLayout(update_card)
        update_layout.setContentsMargins(20, 20, 20, 20)
        update_layout.setSpacing(15)

        update_title = QLabel("SISTEMA")
        update_title.setProperty("role", "section")
        update_layout.addWidget(update_title)

        check_update_layout = QHBoxLayout()
        lbl_update = QLabel("Buscar e instalar nuevas versiones de la aplicación")
        lbl_update.setProperty("role", "subtitle")

        # 3. Uso del ModernButton (Variante Éxito)
        self.btn_update = ModernButton("Buscar actualizaciones", role="action_success")
        self.btn_update.clicked.connect(self.check_update_requested.emit)

        check_update_layout.addWidget(lbl_update)
        check_update_layout.addStretch()
        check_update_layout.addWidget(self.btn_update)

        update_layout.addLayout(check_update_layout)
        layout.addWidget(update_card)

        layout.addStretch() # Empuja todo hacia arriba

    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.setChecked(enabled)