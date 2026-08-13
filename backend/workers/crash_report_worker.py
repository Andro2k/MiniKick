# backend\workers\crash_report_worker.py

import logging
import os
import requests
from PySide6.QtCore import QThread, Signal
from backend.config.api_keys import DISCORD_WEBHOOK_URL
from backend.config.version import APP_VERSION

class CrashReportWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, traceback_text: str, contact: str, description: str, i18n):
        super().__init__()
        self.traceback_text = traceback_text
        self.contact = contact
        self.description = description
        self.i18n = i18n

    def run(self):
        if not DISCORD_WEBHOOK_URL:
            err_msg = self._get_text("crash.err_no_webhook")
            self.finished.emit(False, err_msg)
            return

        try:
            contact_str = self.contact.strip() or self._get_text("crash.anonymous")
            desc_str = self.description.strip() or self._get_text("crash.no_comments")
            
            truncated_tb = self.traceback_text
            if len(truncated_tb) > 1500:
                truncated_tb = truncated_tb[-1500:] + self._get_text("crash.truncated_tb")

            header = self._get_text("crash.header")
            u_label = self._get_text("crash.user_label")
            v_label = self._get_text("crash.version_label")
            a_label = self._get_text("crash.action_label")
            tb_label = self._get_text("crash.traceback_label")

            content = (
                f"{header}\n"
                f"{u_label} {contact_str}\n"
                f"{v_label} {APP_VERSION}\n"
                f"{a_label} {desc_str}\n"
                f"----------------------------------------\n"
                f"{tb_label}\n```python\n{truncated_tb}\n```\n"
                f"----------------------------------------"
            )
            
            payload = {
                "content": content
            }
            
            files = {}
            app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            log_file_path = os.path.join(app_data_dir, '.Minikick', 'logs', 'minikick.log')
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, "rb") as f:
                        files["file"] = ("minikick.log", f.read(), "text/plain")
                except Exception as e:
                    logging.error("[CrashReportWorker] Error reading log: %s", e)

            if files:
                resp = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files, timeout=15)
            else:
                resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)

            if resp.status_code in (200, 204):
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, f"Discord status: {resp.status_code}")
                
        except Exception as e:
            err_tmpl = self._get_text("crash.err_send")
            self.finished.emit(False, err_tmpl.replace("{error}", str(e)))

    def _get_text(self, key: str) -> str:
        if self.i18n:
            return self.i18n.get(key)
        return key

