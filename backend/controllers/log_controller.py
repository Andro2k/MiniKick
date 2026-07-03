# frontend\controllers\log_controller.py

import os
import re
from PySide6.QtCore import QObject, Slot, Signal, QUrl
from PySide6.QtGui import QDesktopServices

class LogController(QObject):
    log_processed = Signal(bool, str, str, str)

    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        
        self._search_term = ""
        self._current_filter = self.view.str_all
        self._is_historical = False
        self._logs_streaming_visible = False
        self._historical_logs = []
        
        self._connect_signals()
        
        self.view.update_display_state(
            is_historical=self._is_historical,
            streaming_visible=self._logs_streaming_visible
        )

    def _connect_signals(self):
        self.view.search_changed.connect(self.handle_search_changed)
        self.view.filter_changed.connect(self.handle_filter_changed)
        self.view.open_folder_requested.connect(self.open_log_folder)
        self.view.load_requested.connect(self.handle_load_requested)
        self.view.live_requested.connect(self.handle_live_requested)
        self.view.clear_requested.connect(self.handle_clear_requested)
        self.view.report_requested.connect(self.open_github_issues)
        self.view.view_toggle_requested.connect(self.handle_view_toggle_requested)
        self.view.view_shown.connect(self.handle_view_shown)

    def _matches_search(self, level: str, time_str: str, text: str) -> bool:
        search_lower = self._search_term.lower()
        if not search_lower:
            return True
        return (search_lower in level.lower() or 
                search_lower in time_str.lower() or 
                search_lower in text.lower())

    def _filter_and_get_logs(self) -> list[tuple[str, str, str]]:
        source = self._historical_logs if self._is_historical else self.service.get_history()
        
        filtered = []
        for lvl, t_str, txt in source:
            is_all = (self._current_filter == self.view.str_all)
            if (is_all or lvl == self._current_filter) and self._matches_search(lvl, t_str, txt):
                filtered.append((lvl, t_str, txt))
        return filtered

    def _refresh_view_logs(self):
        if self._logs_streaming_visible or self._is_historical:
            filtered_logs = self._filter_and_get_logs()
            self.view.display_logs(filtered_logs)
        else:
            self.view.clear_table()

    @Slot(str)
    def handle_search_changed(self, text: str):
        self._search_term = text.strip()
        self._refresh_view_logs()

    @Slot(str)
    def handle_filter_changed(self, filter_text: str):
        self._current_filter = filter_text
        self._refresh_view_logs()

    @Slot()
    def handle_view_toggle_requested(self):
        self._logs_streaming_visible = not self._logs_streaming_visible
        self.view.update_display_state(
            is_historical=self._is_historical,
            streaming_visible=self._logs_streaming_visible
        )
        
        if self._logs_streaming_visible:
            self._refresh_view_logs()
            if hasattr(self.view.window(), "toast"):
                self.view.window().toast.show_toast(
                    title=self.view.i18n.get("log.status.live_title"),
                    message=self.view.i18n.get("log.status.live_msg"),
                    state="info",
                )
        else:
            self.view.clear_table()
            self.view.clear_pending_ops()

    @Slot()
    def handle_view_shown(self):
        if not self._is_historical and self._logs_streaming_visible:
            self._refresh_view_logs()

    @Slot()
    def handle_live_requested(self):
        self._is_historical = False
        self._logs_streaming_visible = False
        self._historical_logs.clear()
        self.view.clear_table()
        self.view.clear_pending_ops()
        self.view.update_display_state(
            is_historical=self._is_historical,
            streaming_visible=self._logs_streaming_visible
        )
        
        if hasattr(self.view.window(), "toast"):
            self.view.window().toast.show_toast(
                title=self.view.i18n.get("log.status.paused_title"),
                message=self.view.i18n.get("log.status.paused_msg"),
                state="success",
            )

    @Slot()
    def handle_clear_requested(self):
        self.service.clear_history()
        self.view.clear_table()
        self.view.clear_pending_ops()
        
        if hasattr(self.view.window(), "toast"):
            self.view.window().toast.show_toast(
                title=self.view.i18n.get("log.status.cleared_title"),
                message=self.view.i18n.get("log.status.cleared_msg"),
                state="info",
            )

    @Slot()
    def handle_load_requested(self):
        default_dir = self.service.log_dir
        file_path = self.view.ask_open_log_file(default_dir)
        if file_path:
            self.read_file(file_path)

    def read_file(self, file_path: str):
        try:
            hist_label = self.view.i18n.get("log.misc.historical")
            parsed_history = self.service.parse_log_file(file_path, hist_label)
            file_name = os.path.basename(file_path)
            
            self._is_historical = True
            self._logs_streaming_visible = True
            self._historical_logs = parsed_history
            
            self.view.update_display_state(
                is_historical=self._is_historical,
                streaming_visible=self._logs_streaming_visible
            )
            self._refresh_view_logs()
            
            if hasattr(self.view.window(), "toast"):
                self.view.window().toast.show_toast(
                    title=self.view.i18n.get("log.status.historical_title"),
                    message=self.view.i18n.get("log.status.historical_msg").replace("{file}", file_name),
                    state="warning",
                )
        except Exception as e:
            error_title = self.view.i18n.get("main.controllers.log.error_title")
            error_msg = self.view.i18n.get("main.controllers.log.read_error").replace("{error}", str(e))
            self.view.show_message("error", error_title, error_msg)

    @Slot(str, str)
    def process_incoming_log(self, level: str, message: str):
        match = re.match(r"\[(.*?)\] \[(.*?)\] (.*)", message, re.DOTALL)
        if match:
            time_str, real_level, text_str = match.groups()
        else:
            time_str, real_level, text_str = "-", level, message

        is_grouped = self.service.append_record(time_str, real_level, text_str)
        self.log_processed.emit(is_grouped, real_level, time_str, text_str)

        if not self._is_historical and self._logs_streaming_visible:
            is_all = (self._current_filter == self.view.str_all)
            if (is_all or real_level == self._current_filter) and self._matches_search(real_level, time_str, text_str):
                self.view.append_log(is_grouped, real_level, time_str, text_str)

    @Slot()
    def open_github_issues(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Andro2k/MiniKick/issues"))
        
    @Slot()
    def open_log_folder(self):
        try:
            folder_url = QUrl.fromLocalFile(self.service.log_dir)
            QDesktopServices.openUrl(folder_url)
        except Exception as e:
            error_title = self.view.i18n.get("main.controllers.log.error_title")
            error_msg = self.view.i18n.get("main.controllers.log.folder_error").replace("{error}", str(e))
            self.view.show_message("error", error_title, error_msg)