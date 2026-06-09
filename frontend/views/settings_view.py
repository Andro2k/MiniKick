# frontend/views/settings_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Signal

from frontend.components.controls import ModernSwitch, ModernButton
from frontend.components.blocks import ViewHeader, SettingRow
from frontend.theme import COLOR_ACCENT, COLOR_DANGER

class SettingsView(QWidget):
    minimize_tray_toggled = Signal(bool)
    unlink_account_requested = Signal()
    check_update_requested = Signal() 

    def __init__(self):
        super().__init__()
        self._setup_ui()

    # =========================================================================
    # ─── CONSTRUCCIÓN DE LA INTERFAZ (Alta Cohesión) ───
    # =========================================================================
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        # ─── 1. ENCABEZADO DE LA VISTA ───
        self.header = ViewHeader(
            title_text="Configuración General", 
            subtitle_text="Ajustes globales del sistema, gestión de cuenta y actualizaciones.", 
            icon_name="settings.svg", 
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        # ─── 2. TARJETA DE SISTEMA Y ACTUALIZACIONES ───
        sys_card = QFrame()
        sys_card.setObjectName("Card")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(18)

        # Fila 1: Minimizar a la bandeja (Switch)
        self.sw_start_bg = ModernSwitch()
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)
        
        row_tray = SettingRow(
            icon_name="minimize.svg", 
            title_text="Ejecución en Segundo Plano", 
            desc_text="Minimizar a la bandeja del sistema en lugar de cerrar la aplicación por completo.", 
            right_widget=self.sw_start_bg
        )

        # Fila 2: Actualizaciones (Botón de Acción Positiva)
        self.btn_update = ModernButton("Buscar actualizaciones", role="action_success")
        self.btn_update.clicked.connect(self.check_update_requested.emit)
        
        row_update = SettingRow(
            icon_name="cloud-download.svg", 
            title_text="Actualizaciones de Software", 
            desc_text="Buscar e instalar nuevas versiones de MiniKick.", 
            right_widget=self.btn_update,
            icon_color=COLOR_ACCENT
        )
        
        sys_layout.addWidget(row_tray)        
        sys_layout.addWidget(row_update)
        self.main_layout.addWidget(sys_card)

        # ─── 3. TARJETA DE GESTIÓN DE CUENTA (Zona de Peligro) ───
        account_card = QFrame()
        account_card.setObjectName("Card")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(20, 20, 20, 20)
        account_layout.setSpacing(18)

        self.btn_unlink = ModernButton("Desvincular", role="action_danger")
        self.btn_unlink.clicked.connect(self.unlink_account_requested.emit)
        
        row_unlink = SettingRow(
            icon_name="user-x.svg", 
            title_text="Desvincular Cuenta", 
            desc_text="Cierra la sesión actual. Tendrás que volver a autorizar a MiniKick la próxima vez.", 
            right_widget=self.btn_unlink,
            icon_color=COLOR_DANGER
        )

        account_layout.addWidget(row_unlink)
        self.main_layout.addWidget(account_card)

        self.main_layout.addStretch()

    # =========================================================================
    # ─── MÉTODOS DE LA LÓGICA DE LA VISTA ───
    # =========================================================================
    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.setChecked(enabled)