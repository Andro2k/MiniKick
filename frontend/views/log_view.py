# frontend\views\log_view.py

import os
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHeaderView, QHBoxLayout, QLabel, QMessageBox,
    QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from frontend.widgets.log_controls_component import LogControlsPanel
from frontend.widgets.blocks_component import ViewHeader
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import COLOR_BLACK, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_INFO, COLOR_WARNING, COLOR_DANGER
from frontend.common.utils import get_assets_path, get_icon_colored

LOG_ILLUSTRATION_FILE = "file-search.svg"

_LEVEL_COLORS = {
    "DEBUG": COLOR_TEXT_SECONDARY,
    "INFO": COLOR_INFO,
    "WARNING": COLOR_WARNING,
    "ERROR": COLOR_DANGER
}
_LEVEL_ICON_NAMES = {
    "DEBUG": "code.svg",
    "INFO": "info-circle.svg",
    "WARNING": "alert-triangle.svg",
    "ERROR": "bug.svg"
}
_LEVEL_ICONS: dict[str, QIcon] = {}

def _get_level_icon(level: str) -> QIcon:
    if level not in _LEVEL_ICONS:
        hex_color = _LEVEL_COLORS.get(level, COLOR_TEXT_PRIMARY)
        icon_name = _LEVEL_ICON_NAMES.get(level, "message.svg")
        _LEVEL_ICONS[level] = get_icon_colored(icon_name, hex_color, 16)
    return _LEVEL_ICONS[level]

class LogView(QWidget):
    search_changed = Signal(str)
    filter_changed = Signal(str)
    open_folder_requested = Signal()
    load_requested = Signal()
    live_requested = Signal()
    clear_requested = Signal()
    report_requested = Signal()
    view_toggle_requested = Signal()
    view_shown = Signal()

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self.str_all = self.i18n.get("log.controls.filter_all")
        self._pending_ui_ops: list[tuple] = []
        self.page_size = 50
        self.current_page = 1
        self.all_logs: list[tuple[str, str, str]] = []
        
        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.setInterval(120)
        self._flush_timer.timeout.connect(self._flush_pending_ui)
        
        self._setup_ui()

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
            icon_color=COLOR_TEXT_PRIMARY,
        )
        self.main_layout.addWidget(self.header)

        self.controls_panel = LogControlsPanel(self.i18n)
        self.controls_panel.search_changed.connect(self.search_changed.emit)
        self.controls_panel.filter_changed.connect(self.filter_changed.emit)
        self.controls_panel.folder_requested.connect(self.open_folder_requested.emit)
        self.controls_panel.load_requested.connect(self.load_requested.emit)
        self.controls_panel.live_requested.connect(self.live_requested.emit)
        self.controls_panel.clear_requested.connect(self.clear_requested.emit)
        self.controls_panel.report_requested.connect(self.report_requested.emit)
        self.controls_panel.view_toggle_requested.connect(self.view_toggle_requested.emit)
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
        self.table.setWordWrap(True)
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
        
        self.pagination_bar = QWidget()
        self.pagination_layout = QHBoxLayout(self.pagination_bar)
        self.pagination_layout.setContentsMargins(12, 8, 12, 8)
        self.pagination_layout.setSpacing(6)
        
        self.lbl_page_info = QLabel()
        self.lbl_page_info.setProperty("role", "body")
        self.pagination_layout.addWidget(self.lbl_page_info)
        
        self.pagination_layout.addStretch(1)
        
        self.btn_prev = ModernButton("", role="action_outlined")
        self.btn_prev.setIcon(get_icon_colored("chevron-left-pipe.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_prev.setFixedWidth(32)
        self.btn_prev.clicked.connect(self.prev_page)
        self.pagination_layout.addWidget(self.btn_prev)
        
        self.page_buttons_container = QWidget()
        self.page_buttons_layout = QHBoxLayout(self.page_buttons_container)
        self.page_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.page_buttons_layout.setSpacing(4)
        self.pagination_layout.addWidget(self.page_buttons_container)
        
        self.btn_next = ModernButton("", role="action_outlined")
        self.btn_next.setIcon(get_icon_colored("chevron-right-pipe.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_next.setFixedWidth(32)
        self.btn_next.clicked.connect(self.next_page)
        self.pagination_layout.addWidget(self.btn_next)
        
        table_page_layout.addWidget(self.pagination_bar)

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
        self.btn_show_logs.clicked.connect(self.view_toggle_requested.emit)

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
        self.table.resizeRowsToContents()
        if hasattr(self, "lbl_illustration") and self.content_stack.currentIndex() == 0:
            card_h = max(self.table_card.height(), 400)
            size = min(max(card_h - 220, 120), 320)
            self._refresh_illustration(size)

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def update_display_state(self, is_historical: bool, streaming_visible: bool):
        show_table = streaming_visible or is_historical
        self.content_stack.setCurrentIndex(1 if show_table else 0)
        self.controls_panel.set_historical_mode(is_historical)
        self.controls_panel.set_view_toggle_state(streaming_visible)
        
        if not show_table and hasattr(self, "lbl_illustration"):
            card_h = max(self.table_card.height(), 400)
            size = min(max(card_h - 220, 120), 320)
            self._refresh_illustration(size)

    def display_logs(self, logs: list[tuple[str, str, str]]):
        self.all_logs = list(logs)
        self.current_page = 1
        self.update_page_display()

    @Slot(bool, str, str, str)
    def append_log(self, is_grouped: bool, level: str, time_str: str, text_str: str):
        self._pending_ui_ops.append((is_grouped, level, time_str, text_str))
        if not self._flush_timer.isActive():
            self._flush_timer.start()

    def clear_table(self):
        self.all_logs.clear()
        self.current_page = 1
        self.update_page_display()

    def clear_pending_ops(self):
        self._flush_timer.stop()
        self._pending_ui_ops.clear()

    def ask_open_log_file(self, default_dir: str) -> str:
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.i18n.get("log.dialogs.select_history"), 
            default_dir, 
            self.i18n.get("log.dialogs.file_filter")
        )
        return file_path

    def _flush_pending_ui(self):
        if not self._pending_ui_ops:
            return
        ops = self._pending_ui_ops
        self._pending_ui_ops = []

        for is_grouped, level, time_str, text_str in ops:
            if is_grouped and self.all_logs:
                lvl, t_str, txt = self.all_logs[-1]
                self.all_logs[-1] = (lvl, t_str, f"{txt}\n{text_str}")
            else:
                self.all_logs.append((level, time_str, text_str))

        if len(self.all_logs) > 1000:
            self.all_logs = self.all_logs[-1000:]

        self.update_page_display()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_page_display()

    def next_page(self):
        total_logs = len(self.all_logs)
        total_pages = max(1, (total_logs + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_page_display()

    def go_to_page(self, page: int):
        self.current_page = page
        self.update_page_display()

    def update_page_buttons(self, total_pages: int):
        while self.page_buttons_layout.count():
            item = self.page_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if total_pages <= 7:
            pages = list(range(1, total_pages + 1))
        else:
            if self.current_page <= 4:
                pages = [1, 2, 3, 4, 5, None, total_pages]
            elif self.current_page >= total_pages - 3:
                pages = [1, None, total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                pages = [1, None, self.current_page - 1, self.current_page, self.current_page + 1, None, total_pages]

        for p in pages:
            if p is None:
                lbl = QLabel("...")
                lbl.setProperty("role", "body")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setFixedWidth(24)
                self.page_buttons_layout.addWidget(lbl)
            else:
                role = "action_accent" if p == self.current_page else "action_outlined"
                btn = ModernButton(str(p), role=role)
                btn.setFixedWidth(32)
                btn.clicked.connect(lambda checked=False, val=p: self.go_to_page(val))
                self.page_buttons_layout.addWidget(btn)

    def update_page_display(self):
        total_logs = len(self.all_logs)
        total_pages = max(1, (total_logs + self.page_size - 1) // self.page_size)

        if self.current_page > total_pages:
            self.current_page = total_pages
        elif self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_logs)

        page_logs = self.all_logs[start_idx:end_idx]

        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(len(page_logs))
        for idx, (lvl, t_str, txt) in enumerate(page_logs):
            self._populate_row_at(idx, lvl, t_str, txt)
        self.table.resizeRowsToContents()
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)

        showing_from = start_idx + 1 if total_logs > 0 else 0
        showing_to = end_idx

        info_text = self.i18n.get("log.pagination.info")
        info_text = info_text.replace("{showing_from}", str(showing_from))
        info_text = info_text.replace("{showing_to}", str(showing_to))
        info_text = info_text.replace("{total}", str(total_logs))
        self.lbl_page_info.setText(info_text)

        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < total_pages)

        self.update_page_buttons(total_pages)

        if self.current_page == total_pages:
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

    def show_message(self, msg_type: str, title: str, text: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Icon.Critical if msg_type == "error" else QMessageBox.Icon.Information)
        msg_box.exec()