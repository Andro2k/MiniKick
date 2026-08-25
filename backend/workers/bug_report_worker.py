# backend\workers\bug_report_worker.py

import logging
import os
import requests
from PySide6.QtCore import QThread, Signal
from backend.config.api_keys import DISCORD_WEBHOOK_URL
from backend.config.version import APP_VERSION

class BugReportWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, username: str, description: str, include_logs: bool, image_path: str, i18n, severity: str = "Low", parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Bug_Report")
        self.username = username
        self.description = description
        self.include_logs = include_logs
        self.image_path = image_path
        self.i18n = i18n
        self.severity = severity

    def run(self):
        if not DISCORD_WEBHOOK_URL:
            self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_no_webhook"))
            return

        try:
            anon_str = self.i18n.get("common.anonymous") if self.i18n else ""
            user_text = self.username.strip() or anon_str
            header = self.i18n.get("dialogs.bug_report.header") if self.i18n else ""
            u_label = self.i18n.get("dialogs.bug_report.user_label") if self.i18n else ""
            v_label = self.i18n.get("dialogs.bug_report.version_label") if self.i18n else ""
            d_label = self.i18n.get("dialogs.bug_report.description_label") if self.i18n else ""
            sev_label = self.i18n.get("dialogs.bug_report.severity_label") if self.i18n else ""
            s_label = f"{sev_label} {self.severity.upper()}"
            content = (
                f"{header}\n"
                f"{u_label} {user_text}\n"
                f"{v_label} {APP_VERSION}\n"
                f"{s_label}\n"
                f"{d_label}\n{self.description}\n"
                f"----------------------------------------"
            )
            data = {
                "content": content
            }


            
            files = {}
            if self.include_logs:
                app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                log_file_path = os.path.join(app_data_dir, '.Minikick', 'logs', 'minikick.log')
                if os.path.exists(log_file_path):
                    try:
                        with open(log_file_path, "rb") as f:
                            files["file"] = ("minikick.log", f.read(), "text/plain")
                    except Exception as e:
                        logging.error("[BugReportWorker] Error reading log file: %s", e)

            if self.image_path and os.path.exists(self.image_path):
                try:
                    filename = os.path.basename(self.image_path)
                    mime_type = "image/png"
                    if filename.lower().endswith((".jpg", ".jpeg")):
                        mime_type = "image/jpeg"
                    elif filename.lower().endswith(".gif"):
                        mime_type = "image/gif"
                    elif filename.lower().endswith(".webp"):
                        mime_type = "image/webp"

                    with open(self.image_path, "rb") as f:
                        files["image"] = (filename, f.read(), mime_type)
                except Exception as e:
                    logging.error("[BugReportWorker] Error reading image file: %s", e)

            if files:
                resp = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=15)
            else:
                resp = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=15)

            if resp.status_code in (200, 204):
                self.finished.emit(True, self.i18n.get("dialogs.bug_report.success_send"))
            else:
                self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_discord").replace("{code}", str(resp.status_code)))
        except Exception as e:
            self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_send").replace("{error}", str(e)))
