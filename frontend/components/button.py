# frontend/components/button.py

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class ModernButton(QPushButton):
    """
    Componente de botón reutilizable.
    Aplica automáticamente el cursor de mano y el rol de estilo del theme.py.
    """
    def __init__(self, text: str, role: str = "action_accent", parent=None):
        super().__init__(text, parent)
        
        # Asignamos la variante de diseño (action_accent, action_outlined, action_danger, etc.)
        self.setProperty("role", role)
        
        # Comportamiento repetitivo centralizado (DRY)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Opcional: Altura estándar para todos los botones principales
        if role in ["action_accent", "action_outlined"]:
            self.setMinimumHeight(38)