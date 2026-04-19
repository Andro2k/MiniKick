# frontend/components/sidebar.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from frontend.theme import Palette, STYLES
from frontend.utils import get_icon_colored

class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.is_expanded = True
        self.width_expanded = 180  # Un poco más ancho para que respire
        self.width_collapsed = 50  # Justo para que el icono de 20px + padding quede centrado
        
        # Diccionarios para manejar los estados de texto e iconos
        self.btn_data = {
            "toggle": {"icon": "menu.svg", "text": " Ocultar Menú"},
            "dash": {"icon": "home.svg", "text": " Dashboard TTS"},
            "pts": {"icon": "star.svg", "text": " Puntos de Canal"}
        }
        
        self.init_ui()

    def init_ui(self):
        self.setObjectName("Sidebar")
        self.setStyleSheet(f"QWidget#Sidebar {{ background-color: {Palette.Black_N2}; border-right: 1px solid {Palette.Black_N3}; }}")
        self.setFixedWidth(self.width_expanded)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 20, 5, 20)
        self.layout.setSpacing(10)

        # Crear botones usando el helper
        self.btn_toggle = self.create_button("toggle")
        self.btn_dashboard = self.create_button("dash")
        self.btn_points = self.create_button("pts")

        # Conexiones
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.btn_dashboard.clicked.connect(lambda: self.change_page(0, self.btn_dashboard))
        self.btn_points.clicked.connect(lambda: self.change_page(1, self.btn_points))

        # Añadir al layout
        self.layout.addWidget(self.btn_toggle)
        self.layout.addSpacing(15)
        self.layout.addWidget(self.btn_dashboard)
        self.layout.addWidget(self.btn_points)
        self.layout.addStretch()

        # Estado inicial
        self.active_button = self.btn_dashboard
        self.update_buttons_style()

    def create_button(self, btn_key):
        """Crea un botón y le asigna su texto e icono inicial."""
        data = self.btn_data[btn_key]
        btn = QPushButton(data["text"])
        btn.setIcon(get_icon_colored(data["icon"], Palette.White_N1, 22))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Se guarda el identificador en el botón para referencias futuras
        btn.setProperty("btn_key", btn_key) 
        return btn

    def get_button_style(self, is_active, is_expanded):
        """Genera el CSS dinámico dependiendo del estado (activo/inactivo) y tamaño (expandido/colapsado)."""
        align = "left" if is_expanded else "center"
        padding = "8px 10px" if is_expanded else "8px 0px" # Sin padding lateral si está colapsado
        
        base_style = f"QPushButton {{ text-align: {align}; padding: {padding}; font-weight: bold; border-radius: 6px; border: none; background: transparent;}}"
        
        if is_active:
            # Color verde + Fondo sutil
            color = Palette.NeonGreen_Main
            extra = f"QPushButton {{ color: {color}; background-color: rgba(83, 252, 24, 0.1); border-left: 3px solid {color}; border-radius: 0px; }}"
        else:
            # Gris apagado
            color = Palette.Gray_N1
            extra = f"QPushButton {{ color: {color}; }} QPushButton:hover {{ background-color: {Palette.White_N2}; color: {Palette.White_N1}; }}"
            
        return base_style + extra

    def update_buttons_style(self):
        """Aplica el estilo a todos los botones según la pestaña activa y si está colapsado o no."""
        for btn in [self.btn_dashboard, self.btn_points]:
            is_active = (btn == self.active_button)
            btn.setStyleSheet(self.get_button_style(is_active, self.is_expanded))
            
            # Repintar el icono del botón activo en Verde (y los inactivos en Blanco)
            key = btn.property("btn_key")
            icon_color = Palette.NeonGreen_Main if is_active else Palette.White_N1
            btn.setIcon(get_icon_colored(self.btn_data[key]["icon"], icon_color, 22))
            
        # El botón toggle siempre mantiene el mismo estilo base, solo cambia la alineación
        self.btn_toggle.setStyleSheet(self.get_button_style(False, self.is_expanded))

    def toggle_sidebar(self):
        # Determinar si vamos a contraer o expandir
        start_w = self.width_expanded if self.is_expanded else self.width_collapsed
        end_w = self.width_collapsed if self.is_expanded else self.width_expanded
        
        # Ocultar textos inmediatamente si colapsamos (para que no salten)
        if self.is_expanded:
            self._set_button_texts("")
            
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200) # Más rápido (de 250 a 200) para mayor fluidez
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine) # Curva más suave
        
        # Al terminar la animación...
        self.animation.finished.connect(self._on_animation_finished)
        self.animation.setStartValue(start_w)
        self.animation.setEndValue(end_w)
        
        self.is_expanded = not self.is_expanded
        self.update_buttons_style() # Actualizar alineación del CSS al instante
        self.animation.start()

    def _on_animation_finished(self):
        """Se ejecuta cuando termina la animación."""
        # Restaurar textos solo si acabamos de expandir
        if self.is_expanded:
            self._set_button_texts(restore=True)

    def _set_button_texts(self, text_override=None, restore=False):
        """Helper para borrar o restaurar los textos de los botones."""
        for btn in [self.btn_toggle, self.btn_dashboard, self.btn_points]:
            key = btn.property("btn_key")
            if restore:
                btn.setText(self.btn_data[key]["text"])
            else:
                btn.setText(text_override)

    def change_page(self, index, button):
        self.active_button = button
        self.update_buttons_style()
        self.page_changed.emit(index)