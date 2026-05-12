from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout
from PySide6.QtCore import Slot
from frontend.components.controls import ModernButton

class LogView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Cabecera
        header_layout = QHBoxLayout()
        title = QLabel("Registro de Desarrollador (Logs)")
        title.setProperty("role", "title")
        
        self.btn_clear = ModernButton("Limpiar Logs", role="action_outlined")
        self.btn_clear.clicked.connect(self._clear_logs)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_clear)
        layout.addLayout(header_layout)

        # Consola de texto
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleDisplay")
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.console)

    @Slot()
    def _clear_logs(self):
        self.console.clear()

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        """Añade el log con colores según su nivel de severidad."""
        color_map = {
            "DEBUG": "#94A3B8",   # Gris
            "INFO": "#38BDF8",    # Azul claro
            "WARNING": "#FBBF24", # Amarillo
            "ERROR": "#EF4444",   # Rojo
            "CRITICAL": "#DC2626" # Rojo oscuro
        }
        
        color = color_map.get(level, "#FFFFFF")
        # Escapamos el HTML básico para evitar que texto con '<' rompa el formato
        safe_msg = message.replace("<", "&lt;").replace(">", "&gt;")
        
        html_msg = f'<span style="color: {color};">{safe_msg}</span>'
        self.console.append(html_msg)
        
        # Auto-scroll hacia abajo
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())