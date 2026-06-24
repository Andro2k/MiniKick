# frontend/views/log_view.py

import os
import re
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHeaderView,
    QMessageBox,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.components.log_controls_component import LogControlsPanel
from frontend.widgets.blocks_component import ViewHeader
from frontend.common.theme import COLOR_ACCENT
from frontend.common.utils import get_icon_colored


class LogView(QWidget):
    read_file_requested = Signal(str)
    report_bug_requested = Signal()
    restore_live_requested = Signal()
    open_folder_requested = Signal()

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self.str_all = self.i18n.get("log.controls.filter_all")

        self._log_history = []
        self._current_filter = self.str_all
        self._search_term = ""
        self._max_logs = 1000
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

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
        self.controls_panel.folder_requested.connect(
            self.open_folder_requested.emit
        )
        self.controls_panel.load_requested.connect(self._open_file_dialog)
        self.controls_panel.live_requested.connect(self._handle_live_click)
        self.controls_panel.clear_requested.connect(
            lambda: self._clear_logs(show_toast=True)
        )
        self.controls_panel.report_requested.connect(self.report_bug_requested.emit)

        self.main_layout.addWidget(self.controls_panel)

        self.table_card = QFrame()
        self.table_card.setProperty("role", "card")
        self.table_card.setMinimumHeight(400)
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(8, 8, 8, 8)

        self.table = QTableWidget(0, 3)
        col_1 = self.i18n.get("log.table.col_level")
        col_2 = self.i18n.get("log.table.col_time")
        col_3 = self.i18n.get("log.table.col_message")
        self.table.setHorizontalHeaderLabels([col_1, col_2, col_3])

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        h_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
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

    def _open_file_dialog(self):
        app_data_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        log_dir = os.path.join(app_data_dir, ".Minikick", "logs")
        dialog_title = (
            self.i18n.get("log.dialogs.select_history")
        )
        file_filter = (
            self.i18n.get("log.dialogs.file_filter")
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self, dialog_title, log_dir, file_filter
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

    def _process_log_data(
        self, default_level: str, message: str, is_historical: bool = False
    ) -> tuple[bool, str, str, str]:
        match = re.match(r"\[(.*?)\] \[(.*?)\] (.*)", message, re.DOTALL)
        if match:
            time_str, real_level, text_str = match.groups()
        else:
            time_str, real_level, text_str = "-", default_level, message

        is_grouped = False
        if self._log_history:
            last_level, last_time, last_text = self._log_history[-1]
            if last_level == real_level and last_time == time_str:
                self._log_history[-1] = (
                    last_level,
                    last_time,
                    f"{last_text}\n{text_str}",
                )
                is_grouped = True

        if not is_grouped:
            self._log_history.append((real_level, time_str, text_str))
            if not is_historical and len(self._log_history) > self._max_logs:
                self._log_history.pop(0)

        return is_grouped, real_level, time_str, text_str

    def _matches_search(self, level: str, time_str: str, text: str) -> bool:
        search_lower = self._search_term.lower()
        if not search_lower:
            return True
        return (
            search_lower in level.lower()
            or search_lower in time_str.lower()
            or search_lower in text.lower()
        )

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        is_grouped, real_level, time_str, text_str = self._process_log_data(
            level, message, is_historical=False
        )

        if not self.controls_panel.btn_live.isVisible():
            if self._current_filter in (self.str_all, real_level) and self._matches_search(
                real_level, time_str, text_str
            ):
                if is_grouped and self.table.rowCount() > 0:
                    self._update_last_row(text_str)
                else:
                    self._add_single_live_row(real_level, time_str, text_str)
                self._scroll_to_bottom()

    def show_historical_content(self, file_name: str, content: str):
        self._clear_logs(show_toast=False)
        hist_label = self.i18n.get("log.misc.historical")

        for line in content.strip().split("\n"):
            if line.strip():
                self._process_log_data(hist_label, line, is_historical=True)

        self._render_logs()
        self.controls_panel.set_historical_mode(True)

        if hasattr(self.window(), "toast"):
            msg_template = (
                self.i18n.get("log.status.historical_msg")
            )
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.historical_title"),
                message=msg_template.replace("{file}", file_name),
                state="warning",
            )

    def _update_last_row(self, appended_text: str):
        last_row = self.table.rowCount() - 1
        item_msg = self.table.item(last_row, 2)
        if item_msg:
            new_text = f"{item_msg.text()}\n{appended_text}"
            item_msg.setText(new_text)
            self.table.resizeRowToContents(last_row)

    def _populate_row_at(self, row: int, level: str, time_str: str, text: str):
        color_map = {
            "DEBUG": "#94A3B8",
            "INFO": "#38BDF8",
            "WARNING": "#FBBF24",
            "ERROR": "#EF4444",
            "CRITICAL": "#DC2626",
        }
        icon_map = {
            "DEBUG": "code.svg",
            "INFO": "info-circle.svg",
            "WARNING": "alert-triangle.svg",
            "ERROR": "bug.svg",
            "CRITICAL": "shield-half.svg",
        }

        hex_color = color_map.get(level, "#FFFFFF")
        qcolor = QColor(hex_color)
        icon_name = icon_map.get(level, "message.svg")

        item_level = QTableWidgetItem(f"  {level.capitalize()}")
        item_level.setForeground(qcolor)
        item_level.setIcon(get_icon_colored(icon_name, hex_color, 16))

        item_time = QTableWidgetItem(time_str)
        item_time.setForeground(QColor("#94A3B8"))

        item_msg = QTableWidgetItem(text)

        for item in (item_level, item_time, item_msg):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.table.setItem(row, 0, item_level)
        self.table.setItem(row, 1, item_time)
        self.table.setItem(row, 2, item_msg)

    def _add_single_live_row(self, level: str, time_str: str, text: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._populate_row_at(row, level, time_str, text)
        self.table.resizeRowToContents(row)

    def _render_logs(self):
        filtered = [
            (lvl, t_str, txt)
            for lvl, t_str, txt in self._log_history
            if self._current_filter in (self.str_all, lvl)
            and self._matches_search(lvl, t_str, txt)
        ]

        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)

        self.table.setRowCount(len(filtered))
        for idx, (lvl, t_str, txt) in enumerate(filtered):
            self._populate_row_at(idx, lvl, t_str, txt)

        self.table.resizeRowsToContents()

        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
        self._scroll_to_bottom()

    def restore_live_view_state(self):
        self.controls_panel.set_historical_mode(False)
        self._clear_logs(show_toast=False)

    @Slot()
    def _handle_live_click(self):
        self.restore_live_view_state()
        self.restore_live_requested.emit()
        if hasattr(self.window(), "toast"):
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.live_title"),
                message=self.i18n.get("log.status.live_msg"),
                state="success",
            )

    @Slot()
    def _clear_logs(self, show_toast: bool = True):
        self._log_history.clear()
        self.table.setRowCount(0)
        if show_toast and hasattr(self.window(), "toast"):
            self.window().toast.show_toast(
                title=self.i18n.get("log.status.cleared_title"),
                message=self.i18n.get("log.status.cleared_msg"),
                state="info",
            )

    def _scroll_to_bottom(self):
        scrollbar = self.table.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_message(self, msg_type: str, title: str, text: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        if msg_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()