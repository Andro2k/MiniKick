# frontend/components/segmented_toggle.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

class SegmentedToggle(QWidget):
    """
    Control segmentado reutilizable.
    Emite 'toggled(bool)' con True si la opción derecha es seleccionada.
    """
    toggled = Signal(bool)

    def __init__(self, text_left: str, text_right: str, default_right=False, parent=None):
        super().__init__(parent)
        self.is_right_active = default_right
        self._setup_ui(text_left, text_right)

    def _setup_ui(self, text_left, text_right):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0) # Fundamental: 0 de espaciado para unirlos

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
        """Cambia el estado y notifica si hay un cambio real."""
        if self.is_right_active != is_right:
            self.is_right_active = is_right
            self._update_styles()
            self.toggled.emit(self.is_right_active)

    def isChecked(self) -> bool:
        """Compatibilidad con la API de tu ModernSwitch anterior."""
        return self.is_right_active
        
    def setChecked(self, is_right: bool):
        self.set_state(is_right)

    def _update_styles(self):
        """Actualiza la propiedad QSS y fuerza la recarga visual."""
        self.btn_left.setProperty("active", not self.is_right_active)
        self.btn_right.setProperty("active", self.is_right_active)

        # Refrescar estilos en PySide6
        self.btn_left.style().unpolish(self.btn_left)
        self.btn_left.style().polish(self.btn_left)
        self.btn_right.style().unpolish(self.btn_right)
        self.btn_right.style().polish(self.btn_right)