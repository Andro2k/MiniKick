# frontend/views/settings_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

from frontend.components.switch import ModernSwitch

class SettingsView(QWidget):
    minimize_tray_toggled = Signal(bool)
    unlink_account_requested = Signal() 
    # NUEVA SEÑAL: Emitida cuando el usuario quiere buscar actualizaciones
    check_update_requested = Signal() 

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
        
        self.btn_unlink = QPushButton("Desvincular")
        self.btn_unlink.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_unlink.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ef4444; 
                color: #ef4444;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.1);
            }
        """)
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

        self.btn_update = QPushButton("Buscar actualizaciones")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        # Usamos un color verde neón neutro o el primario de tu tema
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #53ff1a; 
                color: #53ff1a;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(83, 255, 26, 0.1);
            }
        """)
        # Conectamos el clic del botón a la nueva señal
        self.btn_update.clicked.connect(self.check_update_requested.emit)

        check_update_layout.addWidget(lbl_update)
        check_update_layout.addStretch()
        check_update_layout.addWidget(self.btn_update)

        update_layout.addLayout(check_update_layout)
        layout.addWidget(update_card)

        layout.addStretch() # Empuja todo hacia arriba

    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.setChecked(enabled)