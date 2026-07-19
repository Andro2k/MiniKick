# frontend\views\log_view.py

import os
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize, QDate
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHeaderView, QHBoxLayout, QLabel, QMessageBox, QStackedWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QGridLayout, QLineEdit, QBoxLayout, QSizePolicy, QCheckBox, QDateEdit
)
from frontend.widgets import BaseView, ModernTable, ScalableIllustration, ModernButton
from frontend.common.theme import COLOR_BLACK, COLOR_NEUTRAL_200, COLOR_NEUTRAL_400, COLOR_BLUE, COLOR_AMBER, COLOR_RED
from frontend.common.utils import get_assets_path, get_icon_colored, NoWheelComboBox

class LogControlsPanel(QFrame):
    search_changed = Signal(str)
    filter_changed = Signal(str)
    date_changed = Signal(str)
    folder_requested = Signal()
    load_requested = Signal()
    live_requested = Signal()
    clear_requested = Signal()
    report_requested = Signal()
    view_toggle_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self._search = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._search.setSpacing(6)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self.i18n.get("log.controls.search_placeholder"))
        self.txt_search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.txt_search.textChanged.connect(self.search_changed.emit)

        self.combo_filter = NoWheelComboBox()
        self.combo_filter.addItems([
            self.i18n.get("log.controls.filter_all"),
            "INFO", "DEBUG", "WARNING", "ERROR",
        ])
        self.combo_filter.setMinimumWidth(110)
        self.combo_filter.currentTextChanged.connect(self.filter_changed.emit)

        self.chk_date = QCheckBox(self.i18n.get("log.controls.filter_by_date"))
        self.chk_date.toggled.connect(self._on_date_filter_toggled)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setEnabled(False)
        self.date_edit.dateChanged.connect(self._on_date_changed)

        self._search.addWidget(self.txt_search, 1)
        self._search.addWidget(self.combo_filter)
        self._search.addWidget(self.chk_date)
        self._search.addWidget(self.date_edit)
        root.addLayout(self._search)

        self._actions = QGridLayout()
        self._actions.setSpacing(6)
        root.addLayout(self._actions)

        specs = [
            ("btn_open_folder", self.i18n.get("log.controls.btn_folder"), "action_neutral_border",
             "folder-open.svg", COLOR_NEUTRAL_200, self.folder_requested.emit, True),
            ("btn_load_file", self.i18n.get("log.controls.btn_load"), "action_neutral_border",
             "file-text.svg", COLOR_NEUTRAL_200, self.load_requested.emit, True),
            ("btn_toggle_view", self.i18n.get("log.controls.btn_show_logs"), "action_neutral_border",
             "eye.svg", COLOR_NEUTRAL_200, self.view_toggle_requested.emit, True),
            ("btn_live", self.i18n.get("log.controls.btn_live"), "action_neutral_border",
             "play.svg", COLOR_NEUTRAL_200, self.live_requested.emit, False),
            ("btn_clear", self.i18n.get("log.controls.btn_clear"), "action_neutral_border",
             "trash.svg", COLOR_NEUTRAL_200, self.clear_requested.emit, True),
            ("btn_report", self.i18n.get("log.controls.btn_report"), "action_neutral_border",
             "help.svg", COLOR_NEUTRAL_200, self.report_requested.emit, True),
        ]

        self._buttons: list[ModernButton] = []
        for name, text, role, icon, color, slot, visible in specs:
            btn = ModernButton(text, role=role)
            btn.setParent(self)
            btn.setIcon(get_icon_colored(icon, color, 16))
            btn.setIconSize(QSize(16, 16))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(slot)
            btn.setVisible(visible)
            setattr(self, name, btn)
            self._buttons.append(btn)
            if name == "btn_open_folder":
                btn.setToolTip(self.i18n.get("log.controls.tooltip_folder"))

        self._reflow_buttons()

    def minimumSizeHint(self) -> QSize:
        return QSize(100, 50)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_buttons()
        self._search.setDirection(
            QBoxLayout.Direction.TopToBottom if self.width() < 480
            else QBoxLayout.Direction.LeftToRight
        )

    def _reflow_buttons(self):
        width = max(self.width(), 320)
        visible = [b for b in self._buttons if not b.isHidden()]
        cols = max(1, min(len(visible), width // 120))

        while self._actions.count() > 0:
            self._actions.takeAt(0)

        for c in range(cols):
            self._actions.setColumnStretch(c, 1)

        for i, btn in enumerate(visible):
            self._actions.addWidget(btn, i // cols, i % cols)

    def set_historical_mode(self, is_historical: bool):
        self.btn_live.setVisible(is_historical)
        self.btn_toggle_view.setVisible(not is_historical)
        self.btn_clear.setEnabled(not is_historical)
        self._reflow_buttons()

    def set_streaming_controls_enabled(self, enabled: bool):
        self.txt_search.setEnabled(enabled)
        self.combo_filter.setEnabled(enabled)
        if not self.btn_live.isVisible():
            self.btn_clear.setEnabled(enabled)

    def set_view_toggle_state(self, logs_visible: bool):
        key = "log.controls.btn_hide_logs" if logs_visible else "log.controls.btn_show_logs"
        self.btn_toggle_view.setText(self.i18n.get(key))
        self.set_streaming_controls_enabled(logs_visible)

    def _on_date_filter_toggled(self, checked: bool):
        self.date_edit.setEnabled(checked)
        self.date_changed.emit(self.date_edit.date().toString("yyyy-MM-dd") if checked else "")

    def _on_date_changed(self, qdate: QDate):
        if self.chk_date.isChecked():
            self.date_changed.emit(qdate.toString("yyyy-MM-dd"))

LOG_ILLUSTRATION_FILE = "file-search.svg"
_LEVEL_COLORS = {
    "DEBUG": COLOR_NEUTRAL_400,
    "INFO": COLOR_BLUE,
    "WARNING": COLOR_AMBER,
    "ERROR": COLOR_RED
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
        hex_color = _LEVEL_COLORS.get(level, COLOR_NEUTRAL_200)
        icon_name = _LEVEL_ICON_NAMES.get(level, "message.svg")
        _LEVEL_ICONS[level] = get_icon_colored(icon_name, hex_color, 16)
    return _LEVEL_ICONS[level]

class LogView(BaseView):
    search_changed = Signal(str)
    filter_changed = Signal(str)
    date_changed = Signal(str)
    open_folder_requested = Signal()
    load_requested = Signal()
    live_requested = Signal()
    clear_requested = Signal()
    report_requested = Signal()
    view_toggle_requested = Signal()
    view_shown = Signal()

    def __init__(self, i18n):
        super().__init__(i18n=i18n,title_key="log.header.title",subtitle_key="log.header.subtitle")
        self.str_all = self.i18n.get("log.controls.filter_all")
        self._pending_ui_ops: list[tuple] = []
        self.page_size = 50
        self.current_page = 1
        self.all_logs: list[tuple[str, str, str]] = []
        
        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.setInterval(120)
        self._flush_timer.timeout.connect(self._flush_pending_ui)
        self._page_btn_pool: list[ModernButton] = []
        
        self._setup_ui()

    def _setup_ui(self):
        self.controls_panel = LogControlsPanel(self.i18n)
        self.controls_panel.search_changed.connect(self.search_changed.emit)
        self.controls_panel.filter_changed.connect(self.filter_changed.emit)
        self.controls_panel.date_changed.connect(self.date_changed.emit)
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

        col_1 = self.i18n.get("log.table.col_level")
        col_2 = self.i18n.get("log.table.col_time")
        col_3 = self.i18n.get("log.table.col_message")

        self.table = ModernTable([col_1, col_2, col_3])
        self.table.setWordWrap(True)

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        table_page_layout.addWidget(self.table)
        
        self.pagination_bar = QWidget()
        self.pagination_layout = QHBoxLayout(self.pagination_bar)
        self.pagination_layout.setContentsMargins(8, 8, 8, 8)
        self.pagination_layout.setSpacing(6)
        
        self.btn_prev = ModernButton("", role="action_outlined")
        self.btn_prev.setIcon(get_icon_colored("chevron-left-pipe.svg", COLOR_NEUTRAL_200, 16))
        self.btn_prev.setIconSize(QSize(16, 16))
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(self.prev_page)
        self.pagination_layout.addWidget(self.btn_prev)
        
        self.page_buttons_container = QWidget()
        self.page_buttons_layout = QHBoxLayout(self.page_buttons_container)
        self.page_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.page_buttons_layout.setSpacing(4)
        self.pagination_layout.addWidget(self.page_buttons_container)
        
        self.btn_next = ModernButton("", role="action_outlined")
        self.btn_next.setIcon(get_icon_colored("chevron-right-pipe.svg", COLOR_NEUTRAL_200, 16))
        self.btn_next.setIconSize(QSize(16, 16))
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(self.next_page)
        self.pagination_layout.addWidget(self.btn_next)
        
        self.pagination_layout.addStretch(1)
        
        self.lbl_page_info = QLabel()
        self.lbl_page_info.setProperty("role", "body")
        self.pagination_layout.addWidget(self.lbl_page_info)
        
        table_page_layout.addWidget(self.pagination_bar)

        self.content_stack.addWidget(table_page)
        table_layout.addWidget(self.content_stack)

        self.main_layout.addWidget(self.table_card, stretch=1)

    def _build_empty_state(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        illustration_path = get_assets_path(os.path.join("icons", LOG_ILLUSTRATION_FILE))
        self.lbl_illustration = ScalableIllustration(
            icon_path=illustration_path,
            aspect_ratio=460/750,
            min_size=120,
            max_size=320,
            size_offset=220,
            parent=self
        )

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
        self.btn_show_logs.setIconSize(QSize(16, 16))
        self.btn_show_logs.setFixedWidth(200)
        self.btn_show_logs.clicked.connect(self.view_toggle_requested.emit)

        layout.addStretch(1)
        layout.addWidget(self.lbl_illustration, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addSpacing(8)
        layout.addWidget(self.btn_show_logs, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)

        return container

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table.resizeRowsToContents()
        if hasattr(self, "lbl_illustration") and self.content_stack.currentIndex() == 0:
            card_h = max(self.table_card.height(), 400)
            self.lbl_illustration.update_image(card_h)

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
            self.lbl_illustration.update_image(card_h)

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
        if total_pages <= 7:
            pages = list(range(1, total_pages + 1))
        else:
            if self.current_page <= 4:
                pages = [1, 2, 3, 4, 5, None, total_pages]
            elif self.current_page >= total_pages - 3:
                pages = [1, None, total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                pages = [1, None, self.current_page - 1, self.current_page, self.current_page + 1, None, total_pages]

        while self.page_buttons_layout.count():
            self.page_buttons_layout.takeAt(0)

        pool_idx = 0
        for p in pages:
            if p is None:
                lbl = QLabel("...")
                lbl.setProperty("role", "body")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.page_buttons_layout.addWidget(lbl)
            else:
                role = "action_accent" if p == self.current_page else "action_outlined"
                if pool_idx < len(self._page_btn_pool):
                    btn = self._page_btn_pool[pool_idx]
                    btn.setText(str(p))
                    btn.setProperty("role", role)
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                    try:
                        btn.clicked.disconnect()
                    except RuntimeError:
                        pass
                else:
                    btn = ModernButton(str(p), role=role)
                    self._page_btn_pool.append(btn)
                btn.clicked.connect(lambda checked=False, val=p: self.go_to_page(val))
                btn.setVisible(True)
                self.page_buttons_layout.addWidget(btn)
                pool_idx += 1

        for i in range(pool_idx, len(self._page_btn_pool)):
            self._page_btn_pool[i].setVisible(False)

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
        hex_color = _LEVEL_COLORS.get(level, COLOR_NEUTRAL_200)
        
        item_level = QTableWidgetItem(f"  {level.capitalize()}")
        item_level.setForeground(QColor(hex_color))
        item_level.setIcon(_get_level_icon(level))

        item_time = QTableWidgetItem(time_str)
        item_time.setForeground(QColor(COLOR_NEUTRAL_400))

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

    def show_bug_report_dialog(self):
        from frontend.dialogs.bug_report_dialog import BugReportDialog
        dialog = BugReportDialog(self.i18n, parent=self.window())
        dialog.exec()
