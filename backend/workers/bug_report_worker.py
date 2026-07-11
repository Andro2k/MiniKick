# backend\workers\bug_report_worker.py

import logging
import os
import requests
from PySide6.QtCore import QThread, Signal
from backend.config.api_keys import DISCORD_WEBHOOK_URL
from backend.config.version import APP_VERSION

class BugReportWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, username: str, description: str, include_logs: bool, image_path: str, i18n):
        super().__init__()
        self.username = username
        self.description = description
        self.include_logs = include_logs
        self.image_path = image_path
        self.i18n = i18n

    def run(self):
        if not DISCORD_WEBHOOK_URL:
            self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_no_webhook"))
            return

        try:
            user_text = self.username.strip() or "Anónimo"
            content = (
                f"**REPORTE DE BUG**\n"
                f"**Usuario/Discord:** {user_text}\n"
                f"**Versión de MiniKick:** {APP_VERSION}\n"
                f"**Descripción:**\n{self.description}\n"
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
