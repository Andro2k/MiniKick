# frontend/sidebar.py
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSpacerItem, QSizePolicy, QWidget, QButtonGroup)
from PySide6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup, QSize, Signal

from frontend.utils import get_icon, get_icon_colored
from frontend.theme import COLOR_TEXT_SECONDARY, COLOR_ACCENT

class Sidebar(QFrame):
    # Señal que avisa al controlador qué vista se solicitó
    view_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        
        # Configuración de dimensiones
        self.is_expanded = True
        self.expanded_width = 250
        self.collapsed_width = 70
        self.setFixedWidth(self.expanded_width)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_tab_clicked)
        
        self.nav_buttons = []
        self._setup_ui()

    def _setup_ui(self):
        """Construye la estructura base sin contenido fijo (Alta Cohesión)"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 20, 12, 20)
        self.main_layout.setSpacing(4)
        
        # --- HEADER ---
        self.header_container = QWidget()
        header_layout = QHBoxLayout(self.header_container)
        header_layout.setContentsMargins(0, 0, 0, 0) 
        
        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(get_icon("logo.svg")) 
        self.logo_btn.setIconSize(QSize(40, 40))
        self.logo_btn.setStyleSheet("border: none; background: transparent;")
        
        self.title_label = QLabel("Folderly")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        
        self.expanded_spacer = QWidget()
        self.expanded_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("NavButton")
        self.toggle_btn.setIcon(get_icon_colored("collapse.svg", COLOR_TEXT_SECONDARY)) 
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        header_layout.addWidget(self.logo_btn)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.expanded_spacer) 
        header_layout.addWidget(self.toggle_btn)
        
        self.main_layout.addWidget(self.header_container)
        self.main_layout.addSpacing(15)
        
        # Espaciador elástico al final
        self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addSpacerItem(self.bottom_spacer)

    # ─── SERVICIOS (Contratos para el Controlador) ───

    def add_tab(self, name, icon_name, is_active=False):
        """Permite al controlador añadir pestañas dinámicamente (Desacoplamiento)"""
        btn_text = f"   {name}"
        btn = QPushButton(btn_text)
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Propiedades para lógica interna
        btn.setProperty("original_text", btn_text)
        btn.setProperty("view_name", name)
        btn.setProperty("icon_name", icon_name)
        
        # Estado inicial del ícono
        icon_color = COLOR_ACCENT if is_active else COLOR_TEXT_SECONDARY
        btn.setIcon(get_icon_colored(icon_name, icon_color))
        btn.setIconSize(QSize(20, 20))
        
        if is_active:
            btn.setChecked(True)
            
        self.button_group.addButton(btn)
        self.nav_buttons.append(btn)
        
        # Insertar antes del espaciador final
        self.main_layout.insertWidget(self.main_layout.count() - 1, btn)

    def toggle_sidebar(self):
        """Orquesta la animación y actualiza el estado visual"""
        self.is_expanded = not self.is_expanded
        
        # 1. Animación de ancho
        target = self.expanded_width if self.is_expanded else self.collapsed_width
        self._run_width_animation(target)
        
        # 2. Actualizar visibilidad de elementos del header
        self.logo_btn.setVisible(self.is_expanded)
        self.title_label.setVisible(self.is_expanded)
        self.expanded_spacer.setVisible(self.is_expanded)
        
        # 3. Actualizar botones de navegación
        icon_name = "collapse.svg" if self.is_expanded else "expand.svg"
        self.toggle_btn.setIcon(get_icon_colored(icon_name, COLOR_TEXT_SECONDARY))
        
        for btn in self.nav_buttons:
            # Si está colapsado, quitamos el texto. Si no, lo restauramos.
            btn.setText(btn.property("original_text") if self.is_expanded else "")
            # Usamos una propiedad dinámica para que el CSS (theme.py) haga el centrado
            btn.setProperty("collapsed", not self.is_expanded)
            btn.style().unpolish(btn) # Refrescar estilo
            btn.style().polish(btn)

    def _run_width_animation(self, target):
        self.anim_group = QParallelAnimationGroup()
        for prop in [b"minimumWidth", b"maximumWidth"]:
            anim = QPropertyAnimation(self, prop)
            anim.setDuration(200)
            anim.setStartValue(self.width())
            anim.setEndValue(target)
            self.anim_group.addAnimation(anim)
        self.anim_group.start()

    def _on_tab_clicked(self, btn):
        """Actualiza colores de íconos y notifica al sistema"""
        for b in self.button_group.buttons():
            color = COLOR_ACCENT if b.isChecked() else COLOR_TEXT_SECONDARY
            b.setIcon(get_icon_colored(b.property("icon_name"), color))
        
        self.view_selected.emit(btn.property("view_name"))