# frontend/controllers/log_controller.py

import os
from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtGui import QDesktopServices

class LogController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self._connect_signals()

    def _connect_signals(self):
        self.view.read_file_requested.connect(self.read_file)
        self.view.report_bug_requested.connect(self.open_github_issues)
        self.view.open_folder_requested.connect(self.open_log_folder)

    @Slot(str)
    def read_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_name = os.path.basename(file_path)
            self.view.show_historical_content(file_name, content)
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