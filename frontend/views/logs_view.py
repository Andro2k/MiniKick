# frontend\views\log_view.py

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QFileDialog, QHeaderView, QHBoxLayout, QLabel, QMessageBox, QTableWidgetItem,
    QWidget, QSizePolicy
)
from frontend.widgets import (
    BaseView, ModernTableCard, ModernButton, 
    SegmentedPagination, NoWheelComboBox
)
from frontend.common import (
    COLOR_NEUTRAL_400, COLOR_NEUTRAL_200, COLOR_BLUE, COLOR_AMBER, COLOR_RED,
    get_icon_colored,
    SPACING_SM,
    MARGIN_MD
)

LOG_ILLUSTRATION_FILE = "illustration-result-no-found.svg"
_LEVEL_COLORS = {
    "DEBUG": COLOR_NEUTRAL_400,
    "INFO": COLOR_BLUE,
    "WARNING": COLOR_AMBER,
    "ERROR": COLOR_RED,
    "CRITICAL": COLOR_RED,
    "CRASH": COLOR_RED,
    "FATAL_CRASH": COLOR_RED,
    "THREAD_CRASH": COLOR_RED,
    "BOOTSTRAP": COLOR_BLUE
}
_LEVEL_ICON_NAMES = {
    "DEBUG": "code-square-filled.svg",
    "INFO": "circle-info-filled.svg",
    "WARNING": "alert-triangle-filled.svg",
    "ERROR": "bug-filled.svg",
    "CRITICAL": "bolt-circle-filled.svg",
    "CRASH": "bolt-circle-filled.svg",
    "FATAL_CRASH": "bolt-circle-filled.svg",
    "THREAD_CRASH": "bolt-circle-filled.svg",
    "BOOTSTRAP": "circle-info-filled.svg"
}
_LEVEL_ICONS: dict[str, QIcon] = {}

def _get_level_icon(level: str) -> QIcon:
    if level not in _LEVEL_ICONS:
        hex_color = _LEVEL_COLORS.get(level, COLOR_NEUTRAL_200)
        icon_name = _LEVEL_ICON_NAMES.get(level, "dialog-filled.svg")
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

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="log.header.title", subtitle_key="log.header.subtitle", parent=parent)
        self.str_all = self.i18n.get("log.controls.filter_all")
        self._pending_ui_ops: list[tuple] = []
        self.page_size = 50
        self.current_page = 1
        self.all_logs: list[tuple[str, str, str]] = []
        self._current_sort: tuple[int, str] | None = None
        
        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.setInterval(120)
        self._flush_timer.timeout.connect(self._flush_pending_ui)
        self._page_btn_pool: list[ModernButton] = []
        self._page_label_pool: list[QLabel] = []
        
        self._setup_ui()

    def _setup_ui(self):
        col_1 = self.i18n.get("log.table.col_level")
        col_2 = self.i18n.get("log.table.col_time")
        col_3 = self.i18n.get("log.table.col_message")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("log.table.title"),
            headers=[col_1, col_2, col_3],
            search_placeholder=self.i18n.get("log.controls.search_placeholder"),
            i18n=self.i18n
        )
        self.table = self.table_card.table
        self.table.setWordWrap(True)
        self.table_page = self.table_card

        self.txt_search = self.table_card.txt_search
        if self.txt_search:
            self.txt_search.textChanged.connect(self.search_changed.emit)

        self.combo_date = NoWheelComboBox()
        self.combo_date.addItem(self.i18n.get("log.controls.date_all"), "")
        self.combo_date.addItem(self.i18n.get("log.controls.date_1d"), "1d")
        self.combo_date.addItem(self.i18n.get("log.controls.date_3d"), "3d")
        self.combo_date.addItem(self.i18n.get("log.controls.date_7d"), "7d")
        self.combo_date.setMinimumWidth(110)
        self.combo_date.currentIndexChanged.connect(self._on_date_changed)
        self.table_card.add_header_control(self.combo_date, insert_before_search=False)

        specs = [
            ("btn_open_folder", self.i18n.get("log.controls.btn_folder"), "action_outlined",
             "folder-open-filled.svg", COLOR_NEUTRAL_400, self.open_folder_requested.emit, True),
            ("btn_load_file", self.i18n.get("log.controls.btn_load"), "action_outlined",
             "file-text-filled.svg", COLOR_NEUTRAL_400, self.load_requested.emit, True),
            ("btn_toggle_view", self.i18n.get("log.controls.btn_show_logs"), "action_outlined",
             "eye-filled.svg", COLOR_NEUTRAL_400, self.view_toggle_requested.emit, True),
            ("btn_live", self.i18n.get("log.controls.btn_live"), "action_outlined",
             "play-filled.svg", COLOR_NEUTRAL_400, self.live_requested.emit, False),
            ("btn_clear", self.i18n.get("log.controls.btn_clear"), "action_outlined",
             "trash-filled.svg", COLOR_NEUTRAL_400, self.clear_requested.emit, True),
            ("btn_report", self.i18n.get("log.controls.btn_report"), "action_outlined",
             "bug-filled.svg", COLOR_NEUTRAL_400, self.report_requested.emit, True),
        ]

        self._action_buttons: list[ModernButton] = []
        for name, text, role, icon, color, slot, visible in specs:
            btn = ModernButton(text, role=role)
            btn.setIcon(get_icon_colored(icon, color, 14))
            btn.setIconSize(QSize(14, 14))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(slot)
            btn.setVisible(visible)
            setattr(self, name, btn)
            self._action_buttons.append(btn)
            if name == "btn_open_folder":
                btn.setToolTip(self.i18n.get("log.controls.tooltip_folder"))
            self.table_card.add_action_button(btn)

        self.filter_header = self.table.enable_filter_header()

        sort_asc_text = self.i18n.get("command.table.filter_sort_asc")
        sort_desc_text = self.i18n.get("command.table.filter_sort_desc")
        all_text = self.i18n.get("command.table.filter_all")

        level_options = [
            {"id": "INFO", "label": "INFO"},
            {"id": "DEBUG", "label": "DEBUG"},
            {"id": "WARNING", "label": "WARNING"},
            {"id": "ERROR", "label": "ERROR"},
            {"id": "CRITICAL", "label": "CRITICAL"},
        ]

        self.filter_header.set_column_filter(
            col_idx=0,
            title=col_1,
            options=level_options,
            all_label=all_text,
            sort_asc_label=sort_asc_text,
            sort_desc_label=sort_desc_text
        )

        self.filter_header.set_column_filter(
            col_idx=1,
            title=col_2,
            options=[],
            all_label=all_text,
            sort_asc_label=sort_asc_text,
            sort_desc_label=sort_desc_text
        )

        self.filter_header.filter_changed.connect(self._on_header_filter_changed)
        self.filter_header.sort_requested.connect(self._on_header_sort_requested)
        self.table_card.clear_filters_requested.connect(self._on_clear_filters_requested)

        self.filter_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 160)

        self.table_card.setup_empty_state(
            title=self.i18n.get("log.empty.title"),
            desc=self.i18n.get("log.empty.desc"),
            icon_name=LOG_ILLUSTRATION_FILE,
            button_text=self.i18n.get("log.empty.btn_show"),
            on_button_clicked=self.view_toggle_requested.emit,
            button_icon="eye-filled.svg"
        )

        self.pagination_bar = QWidget()
        self.pagination_layout = QHBoxLayout(self.pagination_bar)
        self.pagination_layout.setContentsMargins(*MARGIN_MD)
        self.pagination_layout.setSpacing(SPACING_SM)

        self.segmented_pagination = SegmentedPagination(self)
        self.segmented_pagination.first_requested.connect(self.first_page)
        self.segmented_pagination.prev_requested.connect(self.prev_page)
        self.segmented_pagination.next_requested.connect(self.next_page)
        self.segmented_pagination.last_requested.connect(self.last_page)

        self.pagination_layout.addWidget(self.segmented_pagination)
        self.pagination_layout.addStretch(1)

        self.lbl_page_info = QLabel()
        self.lbl_page_info.setProperty("role", "body")
        self.pagination_layout.addWidget(self.lbl_page_info)

        self.table_card.set_footer_widget(self.pagination_bar)
        self.main_layout.addWidget(self.table_card, stretch=1)

    def _on_date_changed(self, index: int):
        val = self.combo_date.itemData(index)
        self.date_changed.emit(val if val is not None else "")

    def _on_clear_filters_requested(self):
        if hasattr(self, "filter_header") and self.filter_header:
            self.filter_header.reset_filters()
        self.current_page = 1
        self.update_page_display()

    def _on_header_filter_changed(self, filters: dict):
        self.current_page = 1
        self.update_page_display()

    def _on_header_sort_requested(self, col_idx: int, order: str):
        self._current_sort = (col_idx, order)
        self.current_page = 1
        self.update_page_display()

    def _get_effective_logs(self) -> list[tuple[str, str, str]]:
        if not hasattr(self, "filter_header") or not self.filter_header:
            return self.all_logs

        active_filters = self.filter_header.get_active_filters()
        level_active = active_filters.get(0, {"INFO", "DEBUG", "WARNING", "ERROR"})

        filtered = []
        for item in self.all_logs:
            lvl, t_str, txt = item
            if level_active and lvl.upper() not in level_active:
                continue
            filtered.append(item)

        if hasattr(self, "_current_sort") and self._current_sort:
            col_idx, order = self._current_sort
            reverse = (order == "desc")
            level_ranks = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            def sort_key(item):
                if col_idx == 0:
                    return level_ranks.get(item[0].upper(), 0)
                elif col_idx == 1:
                    return item[1]
                return 0
            filtered.sort(key=sort_key, reverse=reverse)

        return filtered

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table.resizeRowsToContents()

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def update_display_state(self, is_historical: bool, streaming_visible: bool):
        show_table = streaming_visible or is_historical
        self.table_card.set_empty(not show_table)

        self.btn_live.setVisible(is_historical)
        self.btn_toggle_view.setVisible(not is_historical)
        self.btn_clear.setEnabled(not is_historical and streaming_visible)

        key = "log.controls.btn_hide_logs" if streaming_visible else "log.controls.btn_show_logs"
        self.btn_toggle_view.setText(self.i18n.get(key))

        controls_enabled = streaming_visible or is_historical
        if hasattr(self, "txt_search") and self.txt_search:
            self.txt_search.setEnabled(controls_enabled)
        if hasattr(self, "combo_date") and self.combo_date:
            self.combo_date.setEnabled(controls_enabled)

        self.table_card.reflow_header_actions()

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

    def first_page(self):
        if self.current_page > 1:
            self.current_page = 1
            self.update_page_display()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_page_display()

    def next_page(self):
        effective_logs = self._get_effective_logs()
        total_logs = len(effective_logs)
        total_pages = max(1, (total_logs + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_page_display()

    def last_page(self):
        effective_logs = self._get_effective_logs()
        total_logs = len(effective_logs)
        total_pages = max(1, (total_logs + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page = total_pages
            self.update_page_display()

    def go_to_page(self, page: int):
        self.current_page = page
        self.update_page_display()

    def update_page_display(self):
        effective_logs = self._get_effective_logs()
        total_logs = len(effective_logs)
        total_pages = max(1, (total_logs + self.page_size - 1) // self.page_size)

        if self.current_page > total_pages:
            self.current_page = total_pages
        elif self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_logs)

        page_logs = effective_logs[start_idx:end_idx]

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

        total_all = len(self.all_logs)
        if hasattr(self, "table_card"):
            self.table_card.set_title_count(
                base_title=self.i18n.get("log.table.title"),
                count=total_logs,
                total_count=total_all
            )
            if total_logs == 0 and total_all > 0:
                self.table_card.set_no_results(True)
            else:
                self.table_card.set_no_results(False)

        if total_logs < total_all:
            info_text = self.i18n.get("log.pagination.info_filtered")
            info_text = info_text.replace("{showing_from}", str(showing_from))
            info_text = info_text.replace("{showing_to}", str(showing_to))
            info_text = info_text.replace("{total}", str(total_logs))
            info_text = info_text.replace("{total_all}", str(total_all))
        else:
            info_text = self.i18n.get("log.pagination.info")
            info_text = info_text.replace("{showing_from}", str(showing_from))
            info_text = info_text.replace("{showing_to}", str(showing_to))
            info_text = info_text.replace("{total}", str(total_logs))
        self.lbl_page_info.setText(info_text)

        if hasattr(self, "segmented_pagination"):
            self.segmented_pagination.set_page_info(self.current_page, total_pages)

        if self.current_page == total_pages:
            scrollbar = self.table.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _populate_row_at(self, row: int, level: str, time_str: str, text: str):
        hex_color = _LEVEL_COLORS.get(level, COLOR_NEUTRAL_200)
        icon = _get_level_icon(level)
        item_level = self.table.item(row, 0)
        if not item_level:
            item_level = QTableWidgetItem()
            item_level.setFlags(item_level.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_level)
        item_level.setText(f"  {level.capitalize()}")
        item_level.setForeground(QColor(hex_color))
        item_level.setIcon(icon)

        item_time = self.table.item(row, 1)
        if not item_time:
            item_time = QTableWidgetItem()
            item_time.setFlags(item_time.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_time)
        item_time.setText(time_str)
        item_time.setForeground(QColor(COLOR_NEUTRAL_400))

        item_msg = self.table.item(row, 2)
        if not item_msg:
            item_msg = QTableWidgetItem()
            item_msg.setFlags(item_msg.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_msg)
        item_msg.setText(text)

    def show_message(self, msg_type: str, title: str, text: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Icon.Critical if msg_type == "error" else QMessageBox.Icon.Information)
        msg_box.exec()

    def show_bug_report_dialog(self, worker_class=None, initial_contact: str = ""):
        from frontend.dialogs import BugReportDialog
        dialog = BugReportDialog(self.i18n, worker_class=worker_class, initial_contact=initial_contact, parent=self.window())
        dialog.exec()
