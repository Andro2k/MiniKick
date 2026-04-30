# frontend/components/switch.py

from PySide6.QtWidgets import QAbstractButton, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer

# REGLA APLICADA: Alta Cohesión. Importamos tu utilidad centralizada para rutas.
from frontend.utils import get_assets_path

class ModernSwitch(QAbstractButton):
    """
    Componente Switch que utiliza assets SVG estáticos para los estados ON/OFF.
    Implementado de forma nativa con PySide6 para mantener la cohesión del proyecto.
    """
    
    # REGLA APLICADA: DRY. Delegamos la resolución de la ruta absoluta a utils.py
    SVG_ON_PATH = get_assets_path("icons/switch-on.svg")
    SVG_OFF_PATH = get_assets_path("icons/switch-off.svg")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._default_size = QSize(25, 25)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Inicializamos los renderizadores en PySide6
        self._renderer_on = QSvgRenderer(self.SVG_ON_PATH)
        self._renderer_off = QSvgRenderer(self.SVG_OFF_PATH)

    def sizeHint(self) -> QSize:
        """Sugerencia de tamaño para los layouts."""
        return self._default_size

    def paintEvent(self, event):
        """Dibuja el switch alternando entre los SVGs estáticos."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        target_rect = self.rect()

        target_renderer = self._renderer_on if self.isChecked() else self._renderer_off
        
        # Verificamos si la SVG se cargó correctamente antes de renderizar
        if target_renderer.isValid():
            target_renderer.render(painter, target_rect)
        else:
            # Fallback de seguridad visual (Mantenibilidad)
            placeholder_color = Qt.GlobalColor.magenta if self.isChecked() else Qt.GlobalColor.gray
            painter.fillRect(target_rect, placeholder_color)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, "SVG ERR")

        painter.end()