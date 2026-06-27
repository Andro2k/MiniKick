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
        self._connect_signals()

    def _connect_signals(self):
        self.view.read_file_requested.connect(self.read_file)
        self.view.report_bug_requested.connect(self.open_github_issues)
        self.view.open_folder_requested.connect(self.open_log_folder)
        self.view.clear_history_requested.connect(self.service.clear_history)

    @Slot(str, str)
    def process_incoming_log(self, level: str, message: str):
        match = re.match(r"\[(.*?)\] \[(.*?)\] (.*)", message, re.DOTALL)
        if match:
            time_str, real_level, text_str = match.groups()
        else:
            time_str, real_level, text_str = "-", level, message

        is_grouped = self.service.append_record(time_str, real_level, text_str)
        self.log_processed.emit(is_grouped, real_level, time_str, text_str)

    def get_live_history(self):
        return self.service.get_history()

    @Slot(str)
    def read_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_name = os.path.basename(file_path)
            
            parsed_history = []
            hist_label = self.view.i18n.get("log.misc.historical")
            for line in content.strip().split("\n"):
                if not line.strip(): continue
                match = re.match(r"\[(.*?)\] \[(.*?)\] (.*)", line, re.DOTALL)
                if match:
                    parsed_history.append((match.group(2), match.group(1), match.group(3)))
                else:
                    parsed_history.append((hist_label, "-", line))

            self.view.render_historical_data(file_name, parsed_history)
        except Exception as e:
            error_title = self.view.i18n.get("main.controllers.log.error_title")
            error_msg = self.view.i18n.get("main.controllers.log.read_error").replace("{error}", str(e))
            self.view.show_message("error", error_title, error_msg)

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