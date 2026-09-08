# backend\workers\bug_report_worker.py

import logging
import os
import re
import sys
import requests
from PySide6.QtCore import QThread, Signal
from backend.config import DISCORD_WEBHOOK_URL, APP_VERSION
from backend.services.system import TranslationService

logger = logging.getLogger("minikick.workers.bug_report")

def _sanitize_filename_component(text: str, default: str = "anonymous") -> str:
    if not text:
        return default
    cleaned = re.sub(r'[^\w\-.]+', '_', text.strip())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned or default

class BugReportWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, username: str, description: str, include_logs: bool, image_path: str, i18n=None, severity: str = "Low", parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Bug_Report")
        self.username = username
        self.description = description
        self.include_logs = include_logs
        self.image_path = image_path
        self.i18n = i18n or TranslationService()
        self.severity = severity

    def run(self):
        if not DISCORD_WEBHOOK_URL:
            self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_no_webhook"))
            return

        try:
            anon_str = self.i18n.get("common.anonymous")
            user_text = self.username.strip() or anon_str
            header = self.i18n.get("dialogs.bug_report.header")
            u_label = self.i18n.get("dialogs.bug_report.user_label")
            v_label = self.i18n.get("dialogs.bug_report.version_label")
            d_label = self.i18n.get("dialogs.bug_report.description_label")
            sev_label = self.i18n.get("dialogs.bug_report.severity_label")
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
                        safe_user = _sanitize_filename_component(self.username, default="anonymous")
                        safe_ver = _sanitize_filename_component(APP_VERSION, default="unknown")
                        log_filename = f"minikick_{safe_user}_{safe_ver}.log"

                        log_header = (
                            f"================================================================================\n"
                            f"MINIKICK BUG REPORT LOG\n"
                            f"User / Contact : {self.username.strip() or 'Anonymous'}\n"
                            f"App Version    : {APP_VERSION}\n"
                            f"Platform       : {sys.platform}\n"
                            f"Severity       : {self.severity}\n"
                            f"================================================================================\n\n"
                        ).encode("utf-8")

                        with open(log_file_path, "rb") as f:
                            log_content = log_header + f.read()
                        files["file"] = (log_filename, log_content, "text/plain; charset=utf-8")
                    except Exception as e:
                        logger.error("[BugReportWorker] Error reading log file: %s", e)

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
                    logger.error("[BugReportWorker] Error reading image file: %s", e)

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
