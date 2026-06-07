# frontend/views/settings_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, Signal

from frontend.components.controls import ModernSwitch, ModernButton
from frontend.utils import get_icon_colored
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_DANGER

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
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)

        icon_header = QLabel()
        icon_header.setPixmap(get_icon_colored("settings.svg", COLOR_ACCENT, size=28).pixmap(28, 28))
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        
        title = QLabel("Configuración General")
        title.setProperty("role", "title")
        
        subtitle = QLabel("Ajustes globales del sistema, gestión de cuenta y actualizaciones.")
        subtitle.setProperty("role", "body")
        
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(subtitle)
        
        header_layout.addWidget(icon_header, alignment=Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        
        self.main_layout.addWidget(header_frame)

        # ─── 2. TARJETA DE SISTEMA Y ACTUALIZACIONES ───
        sys_card = QFrame()
        sys_card.setObjectName("Card")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(18)

        # Fila 1: Minimizar a la bandeja (Switch)
        self.sw_start_bg = ModernSwitch()
        self.sw_start_bg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)
        
        row_tray = self._create_switch_row(
            icon_name="minimize.svg", 
            title_text="Ejecución en Segundo Plano", 
            desc_text="Minimizar a la bandeja del sistema en lugar de cerrar la aplicación por completo.", 
            switch_widget=self.sw_start_bg
        )

        # Fila 2: Actualizaciones (Botón de Acción Positiva)
        self.btn_update = ModernButton("Buscar actualizaciones", role="action_success")
        self.btn_update.clicked.connect(self.check_update_requested.emit)
        
        row_update = self._create_action_row(
            icon_name="download.svg", 
            icon_color=COLOR_ACCENT,
            title_text="Actualizaciones de Software", 
            desc_text="Buscar e instalar nuevas versiones de MiniKick.", 
            button_widget=self.btn_update
        )

        sys_layout.addLayout(row_tray)
        
        # Línea divisoria
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("background-color: #333333;")
        sys_layout.addWidget(line1)
        
        sys_layout.addLayout(row_update)
        
        self.main_layout.addWidget(sys_card)

        # ─── 3. TARJETA DE GESTIÓN DE CUENTA (Zona de Peligro) ───
        account_card = QFrame()
        account_card.setObjectName("Card")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(20, 20, 20, 20)
        account_layout.setSpacing(18)

        self.btn_unlink = ModernButton("Desvincular", role="action_danger")
        self.btn_unlink.clicked.connect(self.unlink_account_requested.emit)
        
        row_unlink = self._create_action_row(
            icon_name="user-x.svg", 
            icon_color=COLOR_DANGER,
            title_text="Desvincular Cuenta", 
            desc_text="Cierra la sesión actual. Tendrás que volver a autorizar a MiniKick la próxima vez.", 
            button_widget=self.btn_unlink
        )

        account_layout.addLayout(row_unlink)
        self.main_layout.addWidget(account_card)

        self.main_layout.addStretch()

    # =========================================================================
    # ─── MÉTODOS AUXILIARES DE DISEÑO ESTRUCTURAL (DRY) ───
    # =========================================================================
    def _create_switch_row(self, icon_name: str, title_text: str, desc_text: str, switch_widget: ModernSwitch) -> QHBoxLayout:
        """Crea una fila estandarizada con Icono, Título y Descripción, y un Switch a la derecha."""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, COLOR_TEXT_PRIMARY, size=18).pixmap(18, 18))

        text_v_layout = QVBoxLayout()
        text_v_layout.setSpacing(2)
        
        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "section_small")
        
        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        text_v_layout.addWidget(lbl_title)
        text_v_layout.addWidget(lbl_desc)

        row_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row_layout.addLayout(text_v_layout, stretch=1)
        row_layout.addWidget(switch_widget, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
        return row_layout

    def _create_action_row(self, icon_name: str, icon_color: str, title_text: str, desc_text: str, button_widget: QPushButton) -> QHBoxLayout:
        """Crea una fila estandarizada con Icono (coloreable), Textos, y un Botón de Acción a la derecha."""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=18).pixmap(18, 18))

        text_v_layout = QVBoxLayout()
        text_v_layout.setSpacing(2)
        
        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "section_small")
        
        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        text_v_layout.addWidget(lbl_title)
        text_v_layout.addWidget(lbl_desc)

        row_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row_layout.addLayout(text_v_layout, stretch=1)
        row_layout.addWidget(button_widget, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
        return row_layout

    # =========================================================================
    # ─── MÉTODOS DE LA LÓGICA DE LA VISTA ───
    # =========================================================================
    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.setChecked(enabled)