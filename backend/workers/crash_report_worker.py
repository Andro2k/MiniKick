# backend\workers\crash_report_worker.py

import logging
import os
import re
import sys
import requests
from PySide6.QtCore import QThread, Signal
from backend.config.api_keys import DISCORD_WEBHOOK_URL
from backend.config.version import APP_VERSION

logger = logging.getLogger("minikick.workers.crash_report")

def _sanitize_filename_component(text: str, default: str = "anonymous") -> str:
    if not text:
        return default
    cleaned = re.sub(r'[^\w\-.]+', '_', text.strip())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned or default

class CrashReportWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, traceback_text: str, contact: str, description: str, i18n, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Crash_Report")
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
            crash_dump_path = os.path.join(app_data_dir, '.Minikick', 'logs', 'minikick_crash.log')

            safe_user = _sanitize_filename_component(self.contact, default="anonymous")
            safe_ver = _sanitize_filename_component(APP_VERSION, default="unknown")
            log_filename = f"minikick_crash_{safe_user}_{safe_ver}.log"

            log_header = (
                f"================================================================================\n"
                f"MINIKICK CRASH REPORT LOG\n"
                f"User / Contact : {self.contact.strip() or 'Anonymous'}\n"
                f"App Version    : {APP_VERSION}\n"
                f"Platform       : {sys.platform}\n"
                f"================================================================================\n\n"
            ).encode("utf-8")

            combined_logs = log_header

            if os.path.exists(crash_dump_path):
                try:
                    with open(crash_dump_path, "rb") as cf:
                        dump_bytes = cf.read()
                        if dump_bytes.strip():
                            combined_logs += (
                                b"--- FAULTHANDLER NATIVE CRASH DUMP (minikick_crash.log) ---\n"
                                + dump_bytes
                                + b"\n\n"
                            )
                except Exception as e:
                    logger.debug("[CrashReportWorker] Error reading crash dump: %s", e)

            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, "rb") as f:
                        combined_logs += (
                            b"--- APPLICATION EXECUTION LOG (minikick.log) ---\n"
                            + f.read()
                        )
                except Exception as e:
                    logger.error("[CrashReportWorker] Error reading log: %s", e)

            if len(combined_logs) > len(log_header):
                files["file"] = (log_filename, combined_logs, "text/plain; charset=utf-8")

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
