# frontend/sidebar.py
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSpacerItem, QSizePolicy, QWidget, QButtonGroup)
from PySide6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup, QSize

# Importamos las utilidades y colores de tus archivos
from frontend.utils import get_icon, get_icon_colored
from frontend.theme import COLOR_BORDER_SVELTE, COLOR_TEXT_SECONDARY, COLOR_ACCENT

class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        
        # Variables de estado y tamaños
        self.is_expanded = True
        self.expanded_width = 250
        self.collapsed_width = 70
        
        self.setFixedWidth(self.expanded_width)
        
        # ─── GRUPO DE BOTONES (Para comportamiento de pestañas) ──
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True) # Hace que solo uno pueda estar activo
        self.button_group.buttonClicked.connect(self.update_active_buttons)
        
        # Layout principal del Sidebar
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 20, 12, 20)
        self.layout.setSpacing(4)
        
        # ─── HEADER (Logo + Título + Botón de colapsar) ─────────
        self.header_container = QWidget()
        self.header_layout = QHBoxLayout(self.header_container)
        
        # IMPORTANTE: Quitamos los márgenes para alinear este bloque perfectamente con los botones de abajo
        self.header_layout.setContentsMargins(0, 0, 0, 0) 
        
        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(get_icon("logo.svg")) 
        self.logo_btn.setIconSize(QSize(40, 40))
        self.logo_btn.setStyleSheet("border: none; background: transparent;")
        
        self.title_label = QLabel("Folderly")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        
        # Espaciador para cuando está expandido (empuja el botón a la derecha)
        self.expanded_spacer = QWidget()
        self.expanded_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Botón de colapsar / expandir
        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("NavButton") # Usa exactamente el mismo estilo de theme.py
        self.toggle_btn.setIcon(get_icon_colored("collapse.svg", COLOR_TEXT_SECONDARY)) 
        self.toggle_btn.setIconSize(QSize(20, 20)) # Mismo tamaño de ícono
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(40, 40) # Lo hacemos cuadradito por defecto a la derecha
        self.toggle_btn.setStyleSheet("text-align: center; padding: 0px;") # <-- Centrado forzado
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        self.header_layout.addWidget(self.logo_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.expanded_spacer) 
        self.header_layout.addWidget(self.toggle_btn)
        # Eliminamos el collapsed_spacer, ya no es necesario con el nuevo sistema.
        
        self.layout.addWidget(self.header_container)
        self.layout.addSpacing(15)
        
        self.nav_buttons = []
        
        # ─── SECCIONES ───────────────────────────────
        self.add_nav_button("Home", "home.svg", is_active=True)
        self.add_nav_button("My Folders", "folder.svg")
        self.add_nav_button("Shared Folders", "users.svg")
        
        
        self.add_nav_button("Search", "search.svg") 
        self.add_nav_button("Favourites", "star.svg")
        
        self.layout.addSpacing(10)
        
        
        self.add_nav_button("Settings", "settings.svg")
        self.add_nav_button("Help", "help.svg")
        
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))


    def add_nav_button(self, text, icon_name, is_active=False, extra_text="", color=COLOR_TEXT_SECONDARY, is_tab=True):
        btn_text = f"   {text}{extra_text}"
        btn = QPushButton(btn_text)
        btn.setObjectName("NavButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Guardamos propiedades personalizadas
        btn.setProperty("original_text", btn_text)
        btn.setProperty("icon_name", icon_name)
        btn.setProperty("default_color", color)
        
        if is_tab:
            btn.setCheckable(True)
            self.button_group.addButton(btn) 
            
        icon_color = COLOR_ACCENT if is_active else color
        btn.setIcon(get_icon_colored(icon_name, icon_color))
        btn.setIconSize(QSize(20, 20))
        
        if is_active and is_tab:
            btn.setChecked(True)
            
        self.nav_buttons.append(btn)
        self.layout.insertWidget(self.layout.count() - 1, btn)
        return btn

    def update_active_buttons(self, clicked_btn=None):
        """Redibuja los SVGs. El activo se pinta verde, los demás grises."""
        for btn in self.button_group.buttons():
            icon_name = btn.property("icon_name")
            default_color = btn.property("default_color")
            
            if btn.isChecked():
                btn.setIcon(get_icon_colored(icon_name, COLOR_ACCENT))
            else:
                btn.setIcon(get_icon_colored(icon_name, default_color))

    def toggle_sidebar(self):
        self.is_expanded = not self.is_expanded
        target_width = self.expanded_width if self.is_expanded else self.collapsed_width
        
        self.anim_min = QPropertyAnimation(self, b"minimumWidth")
        self.anim_min.setDuration(200)
        self.anim_min.setStartValue(self.width())
        self.anim_min.setEndValue(target_width)
        
        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_max.setDuration(200)
        self.anim_max.setStartValue(self.width())
        self.anim_max.setEndValue(target_width)
        
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.anim_min)
        self.anim_group.addAnimation(self.anim_max)
        self.anim_group.start()
        
        if self.is_expanded:
            # 1. Expandido: Restauramos el header y sus textos
            self.logo_btn.show()
            self.title_label.show()
            self.expanded_spacer.show()
            
            self.toggle_btn.setIcon(get_icon_colored("collapse.svg", COLOR_TEXT_SECONDARY))
            self.toggle_btn.setFixedSize(40, 40) 
            self.toggle_btn.setStyleSheet("text-align: center; padding: 0px;") # <-- Centrado forzado
            
            for item in self.nav_buttons:
                if isinstance(item, QPushButton):
                    item.setText(item.property("original_text"))
                    item.setStyleSheet("") # Permite que vuelva a usar el text-align: left de theme.py
                elif isinstance(item, QFrame):
                    item.show()
        else:
            # 2. Contraído: Ocultamos elementos y forzamos el centrado
            self.logo_btn.hide()
            self.title_label.hide()
            self.expanded_spacer.hide()
            
            self.toggle_btn.setIcon(get_icon_colored("expand.svg", COLOR_TEXT_SECONDARY)) 
            # Como la barra mide 70px y tiene márgenes de 12px, el botón de colapso ocupa exactamente 46px:
            self.toggle_btn.setFixedSize(46, 40) 
            self.toggle_btn.setStyleSheet("text-align: center; padding: 10px 0px;") 
            
            for item in self.nav_buttons:
                if isinstance(item, QPushButton):
                    item.setText("")
                    # Le inyectamos este estilo CSS temporal para sobreescribir theme.py y centrar el ícono
                    item.setStyleSheet("text-align: center; padding: 10px 0px;")
                elif isinstance(item, QFrame):
                    item.hide()