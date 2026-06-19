# frontend/views/settings_view.py

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QScrollArea, QWidget, QVBoxLayout, QFrame, QFileDialog
from PySide6.QtCore import Qt, Signal
from datetime import datetime

from frontend.components.controls import ModernSwitch, ModernButton
from frontend.components.blocks import ViewHeader, SettingRow
from frontend.theme import COLOR_ACCENT, COLOR_DANGER

class SettingsView(QWidget):
    minimize_tray_toggled = Signal(bool)
    export_clicked = Signal()
    import_clicked = Signal()
    unlink_clicked = Signal()
    update_clicked = Signal()
    language_changed = Signal(str)

    # 1. Inyectamos i18n en el constructor
    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        # 2. Usamos i18n.get() para los textos
        self.header = ViewHeader(
            title_text=self.i18n.get("settings.header.title", "Configuración General"), 
            subtitle_text=self.i18n.get("settings.header.subtitle", "Ajustes globales del sistema, gestión de cuenta y actualizaciones."), 
            icon_name="settings.svg", 
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        sys_card = QFrame()
        sys_card.setProperty("role", "card")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(10, 10, 10, 10)
        sys_layout.setSpacing(10)

        self.sw_start_bg = ModernSwitch()
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)
        
        row_tray = SettingRow(
            icon_name="minimize.svg", 
            title_text=self.i18n.get("settings.system.tray_title", "Ejecución en Segundo Plano"), 
            desc_text=self.i18n.get("settings.system.tray_desc", "Minimizar a la bandeja del sistema en lugar de cerrar la aplicación por completo."), 
            right_widget=self.sw_start_bg
        )

        self.btn_update = ModernButton(self.i18n.get("settings.system.btn_update", "Buscar actualizaciones"), role="action_accent")
        self.btn_update.clicked.connect(self.update_clicked.emit)
        
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Español", "es")
        self.combo_lang.addItem("English", "en")
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)

        row_lang = SettingRow(
            icon_name="globe.svg", 
            title_text=self.i18n.get("settings.system.lang_title", "Idioma de la Aplicación"), 
            desc_text=self.i18n.get("settings.system.lang_desc", "Selecciona el idioma de la interfaz (requiere reiniciar)."), 
            right_widget=self.combo_lang
        )
        
        sys_layout.addWidget(row_lang)
        row_update = SettingRow(
            icon_name="cloud-download.svg", 
            title_text=self.i18n.get("settings.system.update_title", "Actualizaciones de Software"), 
            desc_text=self.i18n.get("settings.system.update_desc", "Buscar e instalar nuevas versiones de MiniKick."), 
            right_widget=self.btn_update,
            icon_color=COLOR_ACCENT
        )
        
        sys_layout.addWidget(row_tray)        
        sys_layout.addWidget(row_update)
        self.main_layout.addWidget(sys_card)

        backup_card = QFrame()
        backup_card.setProperty("role", "card")
        backup_layout = QVBoxLayout(backup_card)
        backup_layout.setContentsMargins(10, 10, 10, 10)
        backup_layout.setSpacing(10)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0) 
        btn_layout.setSpacing(8)
        
        self.btn_export = ModernButton(self.i18n.get("settings.backup.btn_export", "Exportar"), role="action_outlined")
        self.btn_import = ModernButton(self.i18n.get("settings.backup.btn_import", "Importar"), role="action_outlined")
        
        self.btn_export.clicked.connect(self.export_clicked.emit)
        self.btn_import.clicked.connect(self.import_clicked.emit)

        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_export)

        row_backup = SettingRow(
            icon_name="restore.svg", 
            title_text=self.i18n.get("settings.backup.title", "Respaldo de Configuración"), 
            desc_text=self.i18n.get("settings.backup.desc", "Exporta o importa tus alertas, voces y ajustes generales."), 
            right_widget=btn_container 
        )

        backup_layout.addWidget(row_backup)
        self.main_layout.addWidget(backup_card)

        account_card = QFrame()
        account_card.setProperty("role", "card")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(10, 10, 10, 10)
        account_layout.setSpacing(10)

        self.btn_unlink = ModernButton(self.i18n.get("settings.account.btn_unlink", "Desvincular"), role="action_danger")
        self.btn_unlink.clicked.connect(self.unlink_clicked.emit)
        
        row_unlink = SettingRow(
            icon_name="user-x.svg", 
            title_text=self.i18n.get("settings.account.title", "Desvincular Cuenta"), 
            desc_text=self.i18n.get("settings.account.desc", "Cierra la sesión actual. Tendrás que volver a autorizar a MiniKick la próxima vez."), 
            right_widget=self.btn_unlink,
            icon_color=COLOR_DANGER
        )

        account_layout.addWidget(row_unlink)
        self.main_layout.addWidget(account_card)
        
        self.main_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.blockSignals(True)
        self.sw_start_bg.setChecked(enabled)
        self.sw_start_bg.blockSignals(False)

    def ask_save_path(self) -> str:
        default_name = f"MiniKick_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        dialog_title = self.i18n.get("settings.dialogs.export_title", "Exportar Configuración")
        filepath, _ = QFileDialog.getSaveFileName(
            self, dialog_title, default_name, "JSON Files (*.json)"
        )
        return filepath

    def ask_open_path(self) -> str:
        dialog_title = self.i18n.get("settings.dialogs.import_title", "Importar Configuración")
        filepath, _ = QFileDialog.getOpenFileName(
            self, dialog_title, "", "JSON Files (*.json)"
        )
        return filepath
    
    def set_current_language(self, lang_code: str):
        self.combo_lang.blockSignals(True)
        idx = self.combo_lang.findData(lang_code)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.blockSignals(False)

    def _on_language_changed(self, index: int):
        lang_code = self.combo_lang.itemData(index)
        self.language_changed.emit(lang_code)