# frontend/views/settings_view.py

from PySide6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Signal

from frontend.components.controls import ModernSwitch, ModernButton
from frontend.components.blocks import ViewHeader, SettingRow
from frontend.theme import COLOR_ACCENT, COLOR_DANGER

class SettingsView(QWidget):
    minimize_tray_toggled = Signal(bool)
    unlink_account_requested = Signal()
    check_update_requested = Signal() 
    
    # ─── CORRECCIÓN: Definición de las nuevas señales ───
    export_requested = Signal()
    import_requested = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text="Configuración General", 
            subtitle_text="Ajustes globales del sistema, gestión de cuenta y actualizaciones.", 
            icon_name="settings.svg", 
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        # ... (sys_card se mantiene igual) ...
        sys_card = QFrame()
        sys_card.setObjectName("Card")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(10, 10, 10, 10)
        sys_layout.setSpacing(10)

        self.sw_start_bg = ModernSwitch()
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)
        
        row_tray = SettingRow(
            icon_name="minimize.svg", 
            title_text="Ejecución en Segundo Plano", 
            desc_text="Minimizar a la bandeja del sistema en lugar de cerrar la aplicación por completo.", 
            right_widget=self.sw_start_bg
        )

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

        # ─── 4. TARJETA DE RESPALDOS (Corregida) ───
        backup_card = QFrame()
        backup_card.setObjectName("Card")
        backup_layout = QVBoxLayout(backup_card)
        backup_layout.setContentsMargins(10, 10, 10, 10)
        backup_layout.setSpacing(10)

        # CORRECCIÓN: Agrupar botones en un contenedor transparente para pasarlo a SettingRow
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0) # Sin márgenes para que se alinee bien
        btn_layout.setSpacing(8)
        
        self.btn_export = ModernButton("Exportar", role="action_outlined")
        self.btn_import = ModernButton("Importar", role="action_outlined")
        
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.btn_import.clicked.connect(self.import_requested.emit)

        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_export)

        # CORRECCIÓN: Ahora SettingRow maneja la alineación de ambos botones
        row_backup = SettingRow(
            icon_name="restore.svg", 
            title_text="Respaldo de Configuración", 
            desc_text="Exporta o importa tus alertas, voces y ajustes generales.", 
            right_widget=btn_container 
        )

        backup_layout.addWidget(row_backup)
        self.main_layout.addWidget(backup_card) # Añadido correctamente al layout principal

        # ─── 3. TARJETA DE GESTIÓN DE CUENTA ───
        # ... (account_card se mantiene igual) ...
        account_card = QFrame()
        account_card.setObjectName("Card")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(10, 10, 10, 10)
        account_layout.setSpacing(10)

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

    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.setChecked(enabled)