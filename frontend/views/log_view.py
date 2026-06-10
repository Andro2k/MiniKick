from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, QComboBox
from PySide6.QtCore import Slot, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from frontend.components.controls import ModernButton
from frontend.utils import get_icon_colored
from frontend.theme import COLOR_TEXT_PRIMARY

class LogView(QWidget):
    def __init__(self):
        super().__init__()
        self._log_history = [] 
        self._current_filter = "TODOS"
        self._max_logs = 1000
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ─── Cabecera ───
        header_layout = QHBoxLayout()
        title = QLabel("Registro de Desarrollador")
        title.setProperty("role", "title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()

        # Selector de Filtro
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["TODOS", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self.combo_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_filter.currentTextChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.combo_filter)

        # Botón Limpiar
        self.btn_clear = ModernButton("Limpiar", role="action_outlined")
        self.btn_clear.setIcon(get_icon_colored("trash.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_clear.clicked.connect(self._clear_logs)
        header_layout.addWidget(self.btn_clear)

        # Botón Reportar Bug (NUEVO)
        self.btn_report = ModernButton("Reportar Bug", role="action_accent")
        self.btn_report.setIcon(get_icon_colored("help.svg", "#000000", 16))
        self.btn_report.setToolTip("Abrir GitHub Issues")
        self.btn_report.clicked.connect(self._open_github_issues)
        header_layout.addWidget(self.btn_report)

        layout.addLayout(header_layout)

        # ─── Consola de texto ───
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleDisplay")
        layout.addWidget(self.console)

    # =========================================================================
    # ─── LÓGICA DE FILTRADO Y NAVEGACIÓN ───
    # =========================================================================
    @Slot(str)
    def _on_filter_changed(self, filter_text: str):
        self._current_filter = filter_text
        self._render_logs()

    @Slot()
    def _open_github_issues(self):
        """Usa el servicio nativo del OS para abrir el navegador web por defecto."""
        QDesktopServices.openUrl(QUrl("https://github.com/Andro2k/MiniKick/issues"))

    @Slot()
    def _clear_logs(self):
        self._log_history.clear()
        self.console.clear()

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        """Añade el log al historial y decide si debe pintarse inmediatamente."""
        color_map = {
            "DEBUG": "#94A3B8",   # Gris
            "INFO": "#38BDF8",    # Azul claro
            "WARNING": "#FBBF24", # Amarillo
            "ERROR": "#EF4444",   # Rojo
            "CRITICAL": "#DC2626" # Rojo oscuro
        }
        
        color = color_map.get(level, "#FFFFFF")
        safe_msg = message.replace("<", "&lt;").replace(">", "&gt;")
        html_msg = f'<span style="color: {color};">{safe_msg}</span>'
        
        self._log_history.append((level, html_msg))
        if len(self._log_history) > self._max_logs:
            self._log_history.pop(0)
        
        if self._current_filter == "TODOS" or self._current_filter == level:
            self.console.append(html_msg)
            self._scroll_to_bottom()

    def _render_logs(self):
        """Repinta la consola completa basado en el historial y el filtro (Alta Cohesión)."""
        self.console.clear()
        for level, html_msg in self._log_history:
            if self._current_filter == "TODOS" or self._current_filter == level:
                self.console.append(html_msg)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())