# frontend/widgets/sidebar.py
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel

from frontend.theme import SPACING, COLOR_TEXT_PRIMARY, COLOR_ACCENT
from frontend.widgets.components import NavButton, SectionLabel
from frontend.utils import get_icon_colored

class Sidebar(QFrame):
    # Emitirá el nombre del botón al que le demos clic (útil si luego agregas más pantallas)
    tab_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(210) # Un poco más ancho para que respire el texto

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)
        layout.setSpacing(SPACING)

        # ─── HEADER (Logo + Título) ───
        header_layout = QHBoxLayout()
        logo_lbl = QLabel()
        # Si tienes un SVG para el logo, lo usamos. Si no, quedará vacío pero no crasheará.
        logo_qicon = get_icon_colored("kick_logo.svg", COLOR_ACCENT, size=24)
        if not logo_qicon.isNull():
            logo_lbl.setPixmap(logo_qicon.pixmap(24, 24))
        else:
            logo_lbl.setText("▶") # Fallback visual
            logo_lbl.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 20px; font-weight: bold;")

        title_lbl = QLabel("KickBot")
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        
        header_layout.addWidget(logo_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        layout.addSpacing(SPACING)

        # ─── NAVEGACIÓN PRINCIPAL ───
        self.btn_dash = NavButton("Inicio", "home.svg")
        self.btn_dash.setChecked(True) # Seleccionado por defecto
        self.btn_chat = NavButton("Chat en Vivo", "chat.svg")

        layout.addWidget(self.btn_dash)
        layout.addWidget(self.btn_chat)

        layout.addSpacing(SPACING)

        # ─── NAVEGACIÓN SECUNDARIA ───
        layout.addWidget(SectionLabel("Sistema"))
        self.btn_settings = NavButton("Ajustes", "settings.svg")
        layout.addWidget(self.btn_settings)

        layout.addStretch() # Empuja todo hacia arriba

        # ─── LÓGICA DE PESTAÑAS ───
        self.buttons = {
            "dashboard": self.btn_dash,
            "chat": self.btn_chat,
            "settings": self.btn_settings
        }

        # Conectar todos los botones a la misma función
        for key, btn in self.buttons.items():
            btn.clicked.connect(lambda checked=False, k=key: self._on_tab_clicked(k))

    def _on_tab_clicked(self, tab_name: str):
        """Maneja el efecto visual de seleccionar solo una pestaña a la vez"""
        for key, btn in self.buttons.items():
            btn.setChecked(key == tab_name)
        
        self.tab_changed.emit(tab_name)