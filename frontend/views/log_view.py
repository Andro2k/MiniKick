# frontend/views/log_view.py

import re
import os
from PySide6.QtWidgets import (QMessageBox, QWidget, QVBoxLayout, 
                               QHBoxLayout, QComboBox, QFrame, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QLineEdit, QBoxLayout,
                               QScrollArea, QFileDialog)
from PySide6.QtCore import Slot, Qt, Signal
from PySide6.QtGui import QColor

from frontend.components.controls import ModernButton
from frontend.components.blocks import ViewHeader
from frontend.utils import get_icon_colored
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY

class LogView(QWidget):
    read_file_requested = Signal(str)
    report_bug_requested = Signal()
    restore_live_requested = Signal()
    open_folder_requested = Signal()

    def __init__(self):
        super().__init__()
        self._log_history = [] 
        self._current_filter = "TODOS"
        self._search_term = ""
        self._max_logs = 1000
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text="Registro de Desarrollador",
            subtitle_text="Monitorea eventos del sistema, depura errores y carga historiales usando el explorador.",
            icon_name="terminal.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self.controls_card = QFrame()
        self.controls_card.setObjectName("Card")
        self.controls_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.controls_card)
        self.controls_layout.setContentsMargins(10, 10, 10, 10)
        self.controls_layout.setSpacing(10)

        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar en los registros...")
        self.txt_search.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.txt_search, stretch=1)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["TODOS", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self.combo_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_filter.currentTextChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self.combo_filter)

        self.controls_layout.addLayout(search_layout, stretch=1)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_open_folder = ModernButton("Carpeta", role="action_outlined")
        self.btn_open_folder.setIcon(get_icon_colored("folder.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_open_folder.setToolTip("Abrir ubicación en Windows")
        self.btn_open_folder.clicked.connect(self.open_folder_requested.emit)

        self.btn_load_file = ModernButton("Cargar Histórico", role="action_outlined")
        self.btn_load_file.setIcon(get_icon_colored("file-text.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_load_file.clicked.connect(self._open_file_dialog)

        self.btn_live = ModernButton("Ver en Vivo", role="action_success")
        self.btn_live.setIcon(get_icon_colored("play.svg", COLOR_ACCENT, 16))
        self.btn_live.clicked.connect(self._handle_live_click)
        self.btn_live.setVisible(False)

        self.btn_clear = ModernButton("Limpiar", role="action_outlined")
        self.btn_clear.setIcon(get_icon_colored("trash.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_clear.clicked.connect(self._clear_logs)

        self.btn_report = ModernButton("Reportar", role="action_accent")
        self.btn_report.setIcon(get_icon_colored("help.svg", "#000000", 16))
        self.btn_report.clicked.connect(self.report_bug_requested.emit)

        actions_layout.addWidget(self.btn_open_folder)
        actions_layout.addWidget(self.btn_load_file)
        actions_layout.addWidget(self.btn_live)
        actions_layout.addWidget(self.btn_clear)
        actions_layout.addWidget(self.btn_report)

        self.controls_layout.addLayout(actions_layout)
        self.main_layout.addWidget(self.controls_card)

        self.table_card = QFrame()
        self.table_card.setObjectName("Card")
        self.table_card.setMinimumHeight(400)
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Log Level", "Timestamp", "Log Message"])
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          
        
        self.table.verticalHeader().setVisible(False) 
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)

        table_layout.addWidget(self.table)
        self.main_layout.addWidget(self.table_card, stretch=1)

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def resizeEvent(self, event):
        """Si la ventana se hace pequeña, apila los controles para no bloquear el redimensionamiento."""
        super().resizeEvent(event)
        if hasattr(self, 'controls_layout'):
            if self.width() < 800:
                self.controls_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            else:
                self.controls_layout.setDirection(QBoxLayout.Direction.LeftToRight)

    def _open_file_dialog(self):
        """Abre la ventana de selección de Windows directamente en la carpeta de logs."""
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(app_data_dir, '.Minikick', 'logs')
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Histórico de Logs", log_dir, "Archivos Log (*.log*);;Todos los archivos (*.*)"
        )
        if file_path:
            self.read_file_requested.emit(file_path)

    @Slot(str)
    def _on_search_changed(self, text: str):
        self._search_term = text.strip()
        self._render_logs()

    @Slot(str)
    def _on_filter_changed(self, filter_text: str):
        self._current_filter = filter_text
        self._render_logs()

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        match = re.match(r"\[(.*?)\] \[(.*?)\] (.*)", message, re.DOTALL)
        if match:
            time_str, real_level, text_str = match.groups()
        else:
            time_str, real_level, text_str = "-", level, message

        self._log_history.append((real_level, time_str, text_str))
        if len(self._log_history) > self._max_logs:
            self._log_history.pop(0)

        if not self.btn_live.isVisible():
            if self._current_filter == "TODOS" or self._current_filter == real_level:
                search_lower = self._search_term.lower()
                if not search_lower or (search_lower in real_level.lower() or 
                                       search_lower in time_str.lower() or 
                                       search_lower in text_str.lower()):
                    self._add_row_to_table(real_level, time_str, text_str)
                    self._scroll_to_bottom()

    def _add_row_to_table(self, level: str, time_str: str, text: str):
        row = self.table.rowCount()
        self.table.insertRow(row)

        color_map = {
            "DEBUG": "#94A3B8",   
            "INFO": "#38BDF8",    
            "WARNING": "#FBBF24", 
            "ERROR": "#EF4444",   
            "CRITICAL": "#DC2626" 
        }
        color_hex = color_map.get(level, "#FFFFFF")
        qcolor = QColor(color_hex)

        icon_char = "◆" if level in ["ERROR", "CRITICAL", "WARNING"] else "●"
        item_level = QTableWidgetItem(f"{icon_char}  {level.capitalize()}")
        item_level.setForeground(qcolor)
        
        item_time = QTableWidgetItem(time_str)
        item_time.setForeground(QColor("#94A3B8"))
        
        item_msg = QTableWidgetItem(text)
        item_msg.setToolTip(text)
        
        for item in (item_level, item_time, item_msg):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.table.setItem(row, 0, item_level)
        self.table.setItem(row, 1, item_time)
        self.table.setItem(row, 2, item_msg)

    def _render_logs(self):
        self.table.setRowCount(0)
        search_lower = self._search_term.lower()
        
        for level, time_str, text in self._log_history:
            if self._current_filter != "TODOS" and self._current_filter != level:
                continue
            if search_lower and (search_lower not in level.lower() and 
                                 search_lower not in time_str.lower() and 
                                 search_lower not in text.lower()):
                continue
                
            self._add_row_to_table(level, time_str, text)
        self._scroll_to_bottom()

    def show_historical_content(self, file_name: str, content: str):
        self._clear_logs()
        self.table.setRowCount(0)
        
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip():
                self.append_log("HISTÓRICO", line)
        
        self.btn_live.setVisible(True)
        self.txt_search.setEnabled(False)
        self.combo_filter.setEnabled(False)
        self.btn_clear.setEnabled(False)

    def restore_live_view_state(self):
        self.btn_live.setVisible(False)
        self.txt_search.setEnabled(True)
        self.combo_filter.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self._clear_logs()

    @Slot()
    def _handle_live_click(self):
        self.restore_live_view_state()
        self.restore_live_requested.emit()

    @Slot()
    def _clear_logs(self):
        self._log_history.clear()
        self.table.setRowCount(0)

    def _scroll_to_bottom(self):
        scrollbar = self.table.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_message(self, msg_type: str, title: str, text: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        if msg_type == "warning": msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "error": msg_box.setIcon(QMessageBox.Icon.Critical)
        else: msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()