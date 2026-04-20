# frontend/components/sidebar.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from frontend.theme import Palette
from frontend.utils import get_icon_colored

class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.is_expanded = True
        self.width_expanded = 190
        self.width_collapsed = 40
        self.category_labels = [] # Guardaremos las etiquetas aquí para ocultarlas luego
        
        self.btn_data = {
            "toggle": {"icon": "menu.svg", "text": " Ocultar Menú"},
            "dash": {"icon": "home.svg", "text": " Dashboard TTS"},
            "pts": {"icon": "layers.svg", "text": " Puntos de Canal"},
            "settings": {"icon": "settings.svg", "text": " Ajustes App"},
            "help": {"icon": "help-circle.svg", "text": " Ayuda / Wiki"}
        }
        
        self.init_ui()

    def init_ui(self):
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.width_expanded)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        # ==========================================
        # 0. BOTÓN TOGGLE (HAMBURGUESA)
        # ==========================================
        self.btn_toggle = self.create_nav_button("toggle", -1) # Index -1 para que no cambie de página
        self.main_layout.addWidget(self.btn_toggle)
        self.main_layout.addSpacing(10)

        # ==========================================
        # 1. PERFIL DE USUARIO
        # ==========================================
        self.profile_frame = QFrame()
        p_lay = QHBoxLayout(self.profile_frame)
        p_lay.setContentsMargins(0, 0, 0, 15)
        
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(get_icon_colored("user.svg", Palette.White_N1, 32).pixmap(32, 32))
        self.avatar_lbl.setStyleSheet(f"background-color: {Palette.Black_N3}; border-radius: 16px; padding: 4px;")
        
        self.user_info_widget = QWidget()
        ui_lay = QVBoxLayout(self.user_info_widget)
        ui_lay.setContentsMargins(10, 0, 0, 0)
        ui_lay.setSpacing(0)
        
        self.user_name = QLabel("Andro Streamer")
        self.user_name.setStyleSheet(f"font-weight: bold; color: {Palette.White_N1}; font-size: 14px;")
        
        self.user_status = QLabel("● En línea")
        self.user_status.setStyleSheet(f"color: {Palette.NeonGreen_Main}; font-size: 11px; font-weight: 600;")
        
        ui_lay.addWidget(self.user_name)
        ui_lay.addWidget(self.user_status)
        p_lay.addWidget(self.avatar_lbl)
        p_lay.addWidget(self.user_info_widget)
        p_lay.addStretch()
        
        self.main_layout.addWidget(self.profile_frame)

        # ==========================================
        # 2. NAVEGACIÓN PRINCIPAL
        # ==========================================
        self.add_category_label("PÁGINAS")
        self.btn_dashboard = self.create_nav_button("dash", 0)
        self.btn_points = self.create_nav_button("pts", 1)
        self.main_layout.addWidget(self.btn_dashboard)
        self.main_layout.addWidget(self.btn_points)

        # ==========================================
        # 3. AJUSTES Y OTROS
        # ==========================================
        self.main_layout.addSpacing(20)
        self.add_category_label("SISTEMA")
        self.btn_settings = self.create_nav_button("settings", 2)
        self.btn_help = self.create_nav_button("help", 3)
        self.main_layout.addWidget(self.btn_settings)
        self.main_layout.addWidget(self.btn_help)

        self.main_layout.addStretch()

        # ==========================================
        # 4. BANNER INFERIOR
        # ==========================================
        self.pro_card = QFrame()
        self.pro_card.setStyleSheet(f"background-color: {Palette.Black_N3}; border-radius: 12px;")
        pro_lay = QVBoxLayout(self.pro_card)
        pro_title = QLabel("MiniKick Studio")
        pro_title.setStyleSheet(f"font-weight: bold; color: {Palette.NeonGreen_Main}; font-size: 12px;")
        pro_desc = QLabel("v0.3 Beta")
        pro_desc.setStyleSheet(f"color: {Palette.Gray_N1}; font-size: 11px;")
        pro_lay.addWidget(pro_title)
        pro_lay.addWidget(pro_desc)
        self.main_layout.addWidget(self.pro_card)

        # Estado inicial
        self.active_button = self.btn_dashboard
        self.update_buttons_style()

    def add_category_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {Palette.Gray_N2}; font-size: 10px; font-weight: bold; padding-left: 5px; margin-top: 10px; margin-bottom: 5px;")
        self.category_labels.append(lbl) # La guardamos en la lista
        self.main_layout.addWidget(lbl)

    def create_nav_button(self, key, index):
        btn = QPushButton(self.btn_data[key]["text"])
        btn.setObjectName("NavBtn") # Asignamos el ID para el QSS
        btn.setIcon(get_icon_colored(self.btn_data[key]["icon"], Palette.Gray_N1, 24))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("btn_key", key)
        
        if key == "toggle":
            btn.clicked.connect(self.toggle_sidebar)
        else:
            btn.clicked.connect(lambda: self.change_page(index, btn))
        return btn

    def update_buttons_style(self):
        for btn in [self.btn_dashboard, self.btn_points, self.btn_settings, self.btn_help]:
            is_active = (btn == self.active_button)
            key = btn.property("btn_key")
            
            # 1. Actualizamos la propiedad
            btn.setProperty("active", is_active)
            
            # 2. Forzamos a Qt a recalcular el estilo
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
            # 3. Solo cambiamos el icono manualmente
            icon_color = Palette.NeonGreen_Main if is_active else Palette.Gray_N1
            btn.setIcon(get_icon_colored(self.btn_data[key]["icon"], icon_color, 24))
            
            # Alineación del texto
            align = "left" if self.is_expanded else "center"
            btn.setStyleSheet(f"text-align: {align};") # Único estilo en línea permitido

    def toggle_sidebar(self):
        start_w = self.width_expanded if self.is_expanded else self.width_collapsed
        end_w = self.width_collapsed if self.is_expanded else self.width_expanded

        if self.is_expanded:
            # 1. Colapsando: Ocultar textos y widgets extra INMEDIATAMENTE
            self._set_button_texts("")
            self.profile_frame.setVisible(False)
            self.pro_card.setVisible(False)
            for lbl in self.category_labels: lbl.setVisible(False)

        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.finished.connect(self._on_animation_finished)
        
        self.animation.setStartValue(start_w)
        self.animation.setEndValue(end_w)
        
        self.is_expanded = not self.is_expanded
        self.update_buttons_style()
        self.animation.start()

    def _on_animation_finished(self):
        if self.is_expanded:
            # 2. Expandiendo: Mostrar widgets extra AL TERMINAR la animación
            self._set_button_texts(restore=True)
            self.profile_frame.setVisible(True)
            self.pro_card.setVisible(True)
            for lbl in self.category_labels: lbl.setVisible(True)

    def _set_button_texts(self, text_override=None, restore=False):
        for btn in [self.btn_toggle, self.btn_dashboard, self.btn_points, self.btn_settings, self.btn_help]:
            key = btn.property("btn_key")
            if restore:
                btn.setText(self.btn_data[key]["text"])
            else:
                btn.setText(text_override)

    def change_page(self, index, button):
        self.active_button = button
        self.update_buttons_style()
        self.page_changed.emit(index)