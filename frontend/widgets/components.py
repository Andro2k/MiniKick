# frontend/widgets/components.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget
)

from frontend.theme import (
    COLOR_ACCENT, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, SPACING
)
from frontend.utils import get_icon_colored

# ── Card ─────────────────────────────────────────────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Conecta con QFrame#Card en theme.py
        self.setObjectName("Card") 
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING * 2, SPACING * 2, SPACING * 2, SPACING * 2)
        self._layout.setSpacing(SPACING)

    def layout(self) -> QVBoxLayout:
        return self._layout

# ── StatCard ─────────────────────────────────────────────────────────────────
class StatCard(Card):
    def __init__(self, label: str, value: str = "—", icon: str = "", parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(SPACING)

        # Si hay ícono, verificamos si es un archivo SVG o un texto/emoji
        if icon:
            icon_lbl = QLabel()
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if icon.endswith(".svg"):
                # Pintamos el SVG de verde usando nuestra utilidad
                qicon = get_icon_colored(icon, COLOR_ACCENT, size=20)
                icon_lbl.setPixmap(qicon.pixmap(20, 20))
                # Estilo base transparente
                icon_lbl.setStyleSheet("background: transparent;")
            else:
                icon_lbl.setText(icon)
                icon_lbl.setObjectName("StatIcon") # Conecta con QLabel#StatIcon en theme.py
                icon_lbl.setFixedSize(32, 32)
                
            top.addWidget(icon_lbl)

        # Etiqueta de título
        lbl = QLabel(label)
        lbl.setProperty("role", "section") # Conecta con QLabel[role="section"]
        top.addWidget(lbl)
        
        # Flex: empuja todo hacia la izquierda
        top.addStretch()

        # Etiqueta de valor grande
        self._value_lbl = QLabel(value)
        self._value_lbl.setProperty("role", "stat_value") # Conecta con QLabel[role="stat_value"]

        self._layout.addLayout(top)
        self._layout.addWidget(self._value_lbl)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)

# ── NavButton ─────────────────────────────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("NavButton") # Conecta con QPushButton#NavButton
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(40)
        
        self._icon_name = icon
        
        # Configurar texto e ícono inicial
        if icon.endswith(".svg"):
            self.setText(f"  {text}")
            # Color por defecto (gris)
            self.setIcon(get_icon_colored(icon, COLOR_TEXT_SECONDARY, size=20))
        else:
            self.setText(f"{icon}  {text}" if icon else f"  {text}")

    # Sobrescribimos setChecked para cambiar el color del SVG dinámicamente
    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        if self._icon_name.endswith(".svg"):
            # Si está seleccionado, verde; si no, gris
            color = COLOR_ACCENT if checked else COLOR_TEXT_SECONDARY
            self.setIcon(get_icon_colored(self._icon_name, color, size=20))

# ── HDivider ─────────────────────────────────────────────────────────────────
class HDivider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("background: #2E3340;") # Borde sutil

# ── SectionLabel ─────────────────────────────────────────────────────────────
class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setProperty("role", "section") # Hereda estilos de theme.py

# ── StatusBadge ──────────────────────────────────────────────────────────────
class StatusBadge(QWidget):
    def __init__(self, text: str = "Offline", color: str = COLOR_TEXT_MUTED, parent=None):
        super().__init__(parent)
        self.setObjectName("TransparentWidget") # Fuerza fondo transparente
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"font-size: 8px; color: {color};")

        self._label = QLabel(text)
        self._label.setStyleSheet(f"font-size: 12px; color: {color};")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch() # Flexbox: Empuja hacia la izquierda

    def set_status(self, text: str, color: str) -> None:
        self._dot.setStyleSheet(f"font-size: 8px; color: {color};")
        self._label.setStyleSheet(f"font-size: 12px; color: {color};")
        self._label.setText(text)

# ── ChatMessage ────────────────────────────────────────────────────────────────
class ChatMessage(QWidget):
    def __init__(self, username: str, message: str, is_highlighted: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("TransparentWidget") # Evita que tenga fondo blanco
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        user_lbl = QLabel(username)
        user_lbl.setFixedWidth(110) # Fija el ancho del nombre para que los mensajes queden alineados
        user_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        user_color = COLOR_ACCENT if is_highlighted else COLOR_TEXT_SECONDARY
        user_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {user_color};")

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True) # ¡Crucial para evitar que mensajes largos rompan el flex!
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # El color base lo toma del theme.py

        layout.addWidget(user_lbl)
        
        # El "1" aquí es el "stretch factor". Actúa como flex-grow: 1, 
        # permitiendo que el mensaje ocupe todo el espacio sobrante.
        layout.addWidget(msg_lbl, 1)