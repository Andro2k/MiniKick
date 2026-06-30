# frontend\views\log_view.py

import os
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHeaderView, QLabel, QMessageBox,
    QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from frontend.widgets.log_controls_component import LogControlsPanel
from frontend.widgets.blocks_component import ViewHeader
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import COLOR_ACCENT, COLOR_BLACK, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_INFO, COLOR_WARNING, COLOR_DANGER
from frontend.common.utils import get_assets_path, get_icon_colored

LOG_ILLUSTRATION_FILE = "file-search.svg"

_LEVEL_COLORS = {
    "DEBUG": COLOR_TEXT_SECONDARY,
    "INFO": COLOR_INFO,
    "WARNING": COLOR_WARNING,
    "ERROR": COLOR_DANGER,
    "CRITICAL": COLOR_DANGER,
}
_LEVEL_ICON_NAMES = {
    "DEBUG": "code.svg",
    "INFO": "info-circle.svg",
    "WARNING": "alert-triangle.svg",
    "ERROR": "bug.svg",
    "CRITICAL": "shield-half.svg",
}
_LEVEL_ICONS: dict[str, QIcon] = {}

def _get_level_icon(level: str) -> QIcon:
    if level not in _LEVEL_ICONS:
        hex_color = _LEVEL_COLORS.get(level, COLOR_TEXT_PRIMARY)
        icon_name = _LEVEL_ICON_NAMES.get(level, "message.svg")
        _LEVEL_ICONS[level] = get_icon_colored(icon_name, hex_color, 16)
    return _LEVEL_ICONS[level]

class LogView(QWidget):
    read_file_requested = Signal(str)
    report_bug_requested = Signal()
    restore_live_requested = Signal()
    open_folder_requested = Signal()
    clear_history_requested = Signal()

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self.str_all = self.i18n.get("log.controls.filter_all")
        self._controller_ref = None
        self._local_display_history = []
        self._current_filter = self.str_all
        self._search_term = ""
        self._pending_ui_ops: list[tuple] = []
        
        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.setInterval(120)
        self._flush_timer.timeout.connect(self._flush_pending_ui)
        
        self._logs_streaming_visible = False
        self._setup_ui()
        self._update_logs_display_mode()

    def set_controller(self, controller):
        self._controller_ref = controller
        self._controller_ref.log_processed.connect(self.append_processed_log)

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text=self.i18n.get("log.header.title"),
            subtitle_text=self.i18n.get("log.header.subtitle"),
            icon_name="brand-tabler.svg",
            icon_color=COLOR_ACCENT,
        )
        self.main_layout.addWidget(self.header)

        self.controls_panel = LogControlsPanel(self.i18n)
        self.controls_panel.search_changed.connect(self._on_search_changed)
        self.controls_panel.filter_changed.connect(self._on_filter_changed)
        self.controls_panel.folder_requested.connect(self.open_folder_requested.emit)
        self.controls_panel.load_requested.connect(self._open_file_dialog)
        self.controls_panel.live_requested.connect(self._handle_live_click)
        self.controls_panel.clear_requested.connect(self._clear_logs)
        self.controls_panel.report_requested.connect(self.report_bug_requested.emit)
        self.controls_panel.view_toggle_requested.connect(self._toggle_logs_view)
        self.main_layout.addWidget(self.controls_panel)

        self.table_card = QFrame()
        self.table_card.setProperty("role", "card")
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_stack = QStackedWidget()
        self.empty_state = self._build_empty_state()
        self.content_stack.addWidget(self.empty_state)

        table_page = QWidget()
        table_page_layout = QVBoxLayout(table_page)
        table_page_layout.setContentsMargins(4, 4, 4, 4)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            self.i18n.get("log.table.col_level"),
            self.i18n.get("log.table.col_time"),
            self.i18n.get("log.table.col_message")
        ])

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        table_page_layout.addWidget(self.table)
        self.content_stack.addWidget(table_page)
        table_layout.addWidget(self.content_stack)

        self.main_layout.addWidget(self.table_card, stretch=1)
        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _build_empty_state(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_illustration = QLabel()
        self.lbl_illustration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_illustration.setScaledContents(True)
        self._illustration_path = get_assets_path(os.path.join("icons", LOG_ILLUSTRATION_FILE))

        lbl_title = QLabel(self.i18n.get("log.empty.title"))
        lbl_title.setProperty("role", "h2")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_desc = QLabel(self.i18n.get("log.empty.desc"))
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setMaximumWidth(450)

        self.btn_show_logs = ModernButton(self.i18n.get("log.empty.btn_show"), role="action_accent")
        self.btn_show_logs.setIcon(get_icon_colored("eye.svg", COLOR_BLACK, 16))
        self.btn_show_logs.setFixedWidth(200)
        self.btn_show_logs.clicked.connect(self._show_live_logs)

        layout.addStretch(1)
        layout.addWidget(self.lbl_illustration, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addSpacing(8)
        layout.addWidget(self.btn_show_logs, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)

        self._refresh_illustration(260)
        return container

    def _refresh_illustration(self, width_size: int):
        if os.path.exists(self._illustration_path):
            icon = QIcon(self._illustration_path)
            height_size = int(width_size * (460 / 750))
            self.lbl_illustration.setPixmap(icon.pixmap(width_size, height_size))
            self.lbl_illustration.setFixedSize(width_size, height_size)
            self.lbl_illustration.setVisible(True)
        else:
            self.lbl_illustration.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "lbl_illustration") and self.content_stack.currentIndex() == 0:
            card_h = max(self.table_card.height(), 400)
            size = min(max(card_h - 220, 120), 320)
            self._refresh_illustration(size)

    def _update_logs_display_mode(self):
        is_historical = self.controls_panel.btn_live.isVisible()
        show_table = self._logs_streaming_visible or is_historical
        self.content_stack.setCurrentIndex(1 if show_table else 0)
        self.controls_panel.set_view_toggle_state(self._logs_streaming_visible)

    @Slot()
    def _toggle_logs_view(self):
        if self._logs_streaming_visible:
            self._hide_live_logs()
        else:
            self._show_live_logs()

    @Slot()
    def _show_live_logs(self):
        self._logs_streaming_visible = True
        self._update_logs_display_mode()
        if self._controller_ref:
            self._local_display_history = list(self._controller_ref.get_live_history())
            self._render_logs()
        if hasattr(self.window(), "toast"):
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.live_title"),
                message=self.i18n.get("log.status.live_msg"),
                state="info",
            )

    @Slot()
    def _hide_live_logs(self):
        self._flush_timer.stop()
        self._pending_ui_ops.clear()
        self._logs_streaming_visible = False
        self.table.setRowCount(0)
        self._update_logs_display_mode()

    def _open_file_dialog(self):
        app_data_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        log_dir = os.path.join(app_data_dir, ".Minikick", "logs")
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.i18n.get("log.dialogs.select_history"), 
            log_dir, 
            self.i18n.get("log.dialogs.file_filter")
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

    @Slot(bool, str, str, str)
    def append_processed_log(self, is_grouped: bool, level: str, time_str: str, text_str: str):
        if not self.controls_panel.btn_live.isVisible() and self._logs_streaming_visible and self.isVisible():
            if self._current_filter in (self.str_all, level) and self._matches_search(level, time_str, text_str):
                self._pending_ui_ops.append((is_grouped, level, time_str, text_str))
                if not self._flush_timer.isActive():
                    self._flush_timer.start()

    def _matches_search(self, level: str, time_str: str, text: str) -> bool:
        search_lower = self._search_term.lower()
        if not search_lower:
            return True
        return (search_lower in level.lower() or search_lower in time_str.lower() or search_lower in text.lower())

    def showEvent(self, event):
        super().showEvent(event)
        if self._logs_streaming_visible and self._controller_ref:
            self._local_display_history = list(self._controller_ref.get_live_history())
            self._render_logs()

    def render_historical_data(self, file_name: str, parsed_history: list[tuple[str, str, str]]):
        self._flush_timer.stop()
        self._pending_ui_ops.clear()
        self._local_display_history = parsed_history
        self._logs_streaming_visible = True
        self._update_logs_display_mode()
        self._render_logs()
        self.controls_panel.set_historical_mode(True)

        if hasattr(self.window(), "toast"):
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.historical_title"),
                message=self.i18n.get("log.status.historical_msg").replace("{file}", file_name),
                state="warning",
            )

    def _flush_pending_ui(self):
        if not self._pending_ui_ops:
            return
        ops = self._pending_ui_ops
        self._pending_ui_ops = []

        self.table.setUpdatesEnabled(False)
        for is_grouped, level, time_str, text_str in ops:
            if is_grouped and self.table.rowCount() > 0:
                last_row = self.table.rowCount() - 1
                item_msg = self.table.item(last_row, 2)
                if item_msg:
                    item_msg.setText(f"{item_msg.text()}\n{text_str}")
            else:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self._populate_row_at(row, level, time_str, text_str)

        if self.table.rowCount() > 0:
            self.table.resizeRowsToContents()
        self.table.setUpdatesEnabled(True)
        scrollbar = self.table.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _populate_row_at(self, row: int, level: str, time_str: str, text: str):
        hex_color = _LEVEL_COLORS.get(level, COLOR_TEXT_PRIMARY)
        
        item_level = QTableWidgetItem(f"  {level.capitalize()}")
        item_level.setForeground(QColor(hex_color))
        item_level.setIcon(_get_level_icon(level))

        item_time = QTableWidgetItem(time_str)
        item_time.setForeground(QColor(COLOR_TEXT_SECONDARY))

        item_msg = QTableWidgetItem(text)

        for item in (item_level, item_time, item_msg):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.table.setItem(row, 0, item_level)
        self.table.setItem(row, 1, item_time)
        self.table.setItem(row, 2, item_msg)

    def _render_logs(self):
        filtered = [
            (lvl, t_str, txt) for lvl, t_str, txt in self._local_display_history
            if self._current_filter in (self.str_all, lvl) and self._matches_search(lvl, t_str, txt)
        ]
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(len(filtered))
        for idx, (lvl, t_str, txt) in enumerate(filtered):
            self._populate_row_at(idx, lvl, t_str, txt)
        self.table.resizeRowsToContents()
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
        scrollbar = self.table.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def restore_live_view_state(self):
        self.controls_panel.set_historical_mode(False)
        self._logs_streaming_visible = False
        self._flush_timer.stop()
        self._pending_ui_ops.clear()
        self._local_display_history.clear()
        self.table.setRowCount(0)
        self._update_logs_display_mode()

    @Slot()
    def _handle_live_click(self):
        self.restore_live_view_state()
        self.restore_live_requested.emit()
        if hasattr(self.window(), "toast"):
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.paused_title"),
                message=self.i18n.get("log.status.paused_msg"),
                state="success",
            )

    @Slot()
    def _clear_logs(self):
        self._flush_timer.stop()
        self._pending_ui_ops.clear()
        self._local_display_history.clear()
        self.table.setRowCount(0)
        self.clear_history_requested.emit()
        if hasattr(self.window(), "toast"):
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.cleared_title"),
                message=self.i18n.get("log.status.cleared_msg"),
                state="info",
            )

    def show_message(self, msg_type: str, title: str, text: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Icon.Critical if msg_type == "error" else QMessageBox.Icon.Information)
        msg_box.exec()