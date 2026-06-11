import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, 
                               QHBoxLayout, QComboBox, QFrame, QListWidget, 
                               QListWidgetItem, QMessageBox)
from PySide6.QtCore import Slot, Qt, QUrl
from PySide6.QtGui import QDesktopServices

from frontend.components.controls import ModernButton
from frontend.utils import get_icon_colored
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY

class LogView(QWidget):
    def __init__(self):
        super().__init__()
        self._log_history = [] 
        self._current_filter = "TODOS"
        self._max_logs = 1000
        self._is_viewing_history = False

        # ─── Acceso al directorio de logs ───
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.log_dir = os.path.join(app_data_dir, '.Minikick', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        self._setup_ui()
        self._load_log_files()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        title = QLabel("Registro de Desarrollador")
        title.setProperty("role", "title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["TODOS", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self.combo_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_filter.currentTextChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.combo_filter)
        
        self.btn_live = ModernButton("Ver en Vivo", role="action_success")
        self.btn_live.setIcon(get_icon_colored("play.svg", COLOR_ACCENT, 16))
        self.btn_live.clicked.connect(self._restore_live_view)
        self.btn_live.setVisible(False)
        header_layout.addWidget(self.btn_live)

        self.btn_clear = ModernButton("Limpiar", role="action_outlined")
        self.btn_clear.setIcon(get_icon_colored("trash.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_clear.clicked.connect(self._clear_logs)
        header_layout.addWidget(self.btn_clear)

        self.btn_report = ModernButton("Reportar Bug", role="action_accent")
        self.btn_report.setIcon(get_icon_colored("help.svg", "#000000", 16))
        self.btn_report.setToolTip("Abrir GitHub Issues")
        self.btn_report.clicked.connect(self._open_github_issues)
        header_layout.addWidget(self.btn_report)

        layout.addLayout(header_layout)

        # ─── Cuerpo Dividido (NUEVO) ───
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # 1. Consola de texto (Izquierda)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleDisplay")
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.console.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) 
        self.console.document().setDocumentMargin(0)

        body_layout.addWidget(self.console, stretch=3)

        # 2. Panel de Archivos Históricos (Derecha)
        files_card = QFrame()
        files_card.setObjectName("Card")
        files_layout = QVBoxLayout(files_card)
        files_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_files = QLabel("Historial de Archivos")
        lbl_files.setProperty("role", "section")
        files_layout.addWidget(lbl_files)

        self.list_files = QListWidget()
        self.list_files.setObjectName("LogFileList")
        self.list_files.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_files.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.list_files.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_files.setTextElideMode(Qt.TextElideMode.ElideRight)
        
        files_layout.addWidget(self.list_files)

        self.btn_refresh = ModernButton("Actualizar Lista", role="action_outlined")
        self.btn_refresh.clicked.connect(self._load_log_files)
        files_layout.addWidget(self.btn_refresh)

        body_layout.addWidget(files_card, stretch=1)
        layout.addLayout(body_layout)

    # =========================================================================
    # ─── LÓGICA DE GESTIÓN DE ARCHIVOS LOG ───
    # =========================================================================
    @Slot()
    def _load_log_files(self):
        self.list_files.clear()
        if not os.path.exists(self.log_dir):
            return

        try:
            files = [f for f in os.listdir(self.log_dir) if f.startswith('minikick.log')]
            files.sort(reverse=True)

            for file_name in files:
                self._add_file_item(file_name)
        except Exception as e:
            self.append_log("ERROR", f"Error al cargar archivos de log: {e}")

    def _add_file_item(self, file_name: str):
        item = QListWidgetItem(self.list_files)
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        btn_read = ModernButton("", role="action_success")
        btn_read.setFixedSize(24, 24)
        btn_read.setIcon(get_icon_colored("eye.svg", COLOR_ACCENT, 14))
        btn_read.setToolTip("Cargar historial en la consola")
        btn_read.clicked.connect(lambda checked, fn=file_name: self._read_log_file(fn))
        layout.addWidget(btn_read)
        
        btn_del = ModernButton("", role="action_danger")
        btn_del.setFixedSize(24, 24)
        btn_del.setIcon(get_icon_colored("trash.svg", "#ef4444", 14))
        btn_del.setToolTip("Eliminar archivo de registro")
        btn_del.clicked.connect(lambda checked, fn=file_name: self._delete_log_file(fn))
        layout.addWidget(btn_del)

        lbl_name = QLabel(file_name)
        lbl_name.setProperty("role", "monospace")
        
        if file_name == "minikick.log":
            lbl_name.setText(f"{file_name} (Activo)")
            lbl_name.setStyleSheet("color: #0ca678; font-weight: bold;")
        
        layout.addWidget(lbl_name)
        
        item.setSizeHint(widget.sizeHint())
        self.list_files.setItemWidget(item, widget)

    @Slot(str)
    def _delete_log_file(self, file_name: str):
        file_path = os.path.join(self.log_dir, file_name)
        try:
            os.remove(file_path)
            self._load_log_files()
            self.append_log("INFO", f"Archivo {file_name} eliminado con éxito.")
        except PermissionError:
            QMessageBox.warning(self, "Archivo en Uso", f"No se puede eliminar '{file_name}' porque la aplicación está escribiendo en él actualmente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar el archivo: {e}")

    @Slot(str)
    def _read_log_file(self, file_name: str):
        file_path = os.path.join(self.log_dir, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._is_viewing_history = True
            self.console.clear()
            self.console.setHtml(f"<h3 style='color: #FBBF24;'>=== MODO LECTURA: {file_name} ===</h3><br>")
            self.console.append(content)
            
            self.btn_live.setVisible(True)
            self.combo_filter.setEnabled(False)
            self.btn_clear.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo: {e}")

    @Slot()
    def _restore_live_view(self):
        """Aplica DRY: Reutiliza _render_logs para restaurar el estado original"""
        self._is_viewing_history = False
        self.btn_live.setVisible(False)
        self.combo_filter.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self._render_logs()

    @Slot(str)
    def _on_filter_changed(self, filter_text: str):
        self._current_filter = filter_text
        self._render_logs()

    @Slot()
    def _open_github_issues(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Andro2k/MiniKick/issues"))

    @Slot()
    def _clear_logs(self):
        self._log_history.clear()
        self.console.clear()

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        color_map = {
            "DEBUG": "#94A3B8",   
            "INFO": "#38BDF8",    
            "WARNING": "#FBBF24", 
            "ERROR": "#EF4444",   
            "CRITICAL": "#DC2626" 
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
        self.console.clear()
        for level, html_msg in self._log_history:
            if self._current_filter == "TODOS" or self._current_filter == level:
                self.console.append(html_msg)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())