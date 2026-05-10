# frontend/components/controls.py

from PySide6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QAbstractButton, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from frontend.utils import get_assets_path

# ─── BOTONES BÁSICOS ─────────────────────────────────────────────────────────
class ModernButton(QPushButton):
    """Componente de botón reutilizable con roles de estilo."""
    def __init__(self, text: str, role: str = "action_accent", parent=None):
        super().__init__(text, parent)
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if role in ["action_accent", "action_outlined"]:
            self.setMinimumHeight(38)


# ─── CONTROLES DE ESTADO (TOGGLES Y SWITCHES) ────────────────────────────────
class SegmentedToggle(QWidget):
    """Control segmentado reutilizable."""
    toggled = Signal(bool)

    def __init__(self, text_left: str, text_right: str, default_right=False, parent=None):
        super().__init__(parent)
        self.is_right_active = default_right
        self._setup_ui(text_left, text_right)

    def _setup_ui(self, text_left, text_right):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_left = QPushButton(text_left)
        self.btn_left.setObjectName("ToggleLeft")
        self.btn_left.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_left.clicked.connect(lambda: self.set_state(False))

        self.btn_right = QPushButton(text_right)
        self.btn_right.setObjectName("ToggleRight")
        self.btn_right.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_right.clicked.connect(lambda: self.set_state(True))

        layout.addWidget(self.btn_left)
        layout.addWidget(self.btn_right)
        self._update_styles()

    def set_state(self, is_right: bool):
        if self.is_right_active != is_right:
            self.is_right_active = is_right
            self._update_styles()
            self.toggled.emit(self.is_right_active)

    def isChecked(self) -> bool:
        return self.is_right_active
        
    def setChecked(self, is_right: bool):
        self.set_state(is_right)

    def _update_styles(self):
        self.btn_left.setProperty("active", not self.is_right_active)
        self.btn_right.setProperty("active", self.is_right_active)
        for btn in (self.btn_left, self.btn_right):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

class ModernSwitch(QAbstractButton):
    """Componente Switch que utiliza assets SVG estáticos."""
    SVG_ON_PATH = get_assets_path("icons/switch-on.svg")
    SVG_OFF_PATH = get_assets_path("icons/switch-off.svg")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._default_size = QSize(25, 25)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self._renderer_on = QSvgRenderer(self.SVG_ON_PATH)
        self._renderer_off = QSvgRenderer(self.SVG_OFF_PATH)

    def sizeHint(self) -> QSize:
        return self._default_size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        target_rect = self.rect()
        target_renderer = self._renderer_on if self.isChecked() else self._renderer_off
        
        if target_renderer.isValid():
            target_renderer.render(painter, target_rect)
        else:
            placeholder_color = Qt.GlobalColor.magenta if self.isChecked() else Qt.GlobalColor.gray
            painter.fillRect(target_rect, placeholder_color)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, "ERR")
        painter.end()