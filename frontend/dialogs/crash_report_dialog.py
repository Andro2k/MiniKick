# frontend\dialogs\crash_report_dialog.py

import os
import requests
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QTextEdit, QPushButton, QApplication
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor

from frontend.dialogs.base_dialog import ModernModal
from frontend.common.utils import get_assets_path
from frontend.common.theme import COLOR_RED
from backend.config.api_keys import DISCORD_WEBHOOK_URL
from backend.config.version import APP_VERSION

class CrashReportDialog(ModernModal):
    def __init__(self, traceback_text: str, i18n=None, parent=None):
        self.traceback_text = traceback_text
        self.i18n = i18n
        self.title_text = self._get_text("crash.title", "MiniKick ha fallado")
        self.lbl_contact_text = self._get_text("crash.lbl_contact", "Contacto / Discord (Opcional)")
        self.placeholder_contact_text = self._get_text("crash.placeholder_contact", "Ej. Andro2k")
        self.lbl_desc_text = self._get_text("crash.lbl_desc", "¿Qué estabas haciendo cuando falló? (Opcional)")
        self.placeholder_desc_text = self._get_text("crash.placeholder_desc", "Describe brevemente los pasos...")
        self.lbl_traceback_text = self._get_text("crash.lbl_traceback", "Detalles del Error (Traceback)")
        self.btn_send_text = self._get_text("crash.btn_send", "Enviar Reporte y Cerrar")
        self.btn_close_text = self._get_text("crash.btn_close", "Cerrar sin Enviar")
        self.err_send_text = self._get_text("crash.err_send", "No se pudo enviar el reporte. Error: {error}")
        self.err_no_webhook_text = self._get_text("crash.err_no_webhook", "URL del Webhook de Discord no configurada.")
        self.subtitle_text = self._get_text(
            "crash.subtitle", 
            "Se produjo un error no controlado en la aplicación. Ayúdanos a solucionar el problema enviando este reporte."
        )

        icon_path = get_assets_path("icons/bug.svg")
        super().__init__(
            title=self.title_text,
            icon_path=icon_path,
            icon_bg_color=COLOR_RED,
            width=520,
            parent=parent
        )
        
        self.set_dialog_state("danger", QColor(239, 68, 68, 80))
        self._setup_crash_form()

    def _get_text(self, key: str, default: str) -> str:
        if self.i18n:
            return self.i18n.get(key) or default
        return default

    def _setup_crash_form(self):
        lbl_subtitle = QLabel(self.subtitle_text)
        lbl_subtitle.setProperty("role", "body")
        lbl_subtitle.setWordWrap(True)
        lbl_subtitle.setStyleSheet("color: #9CA3AF; margin-bottom: 8px;")

        lbl_contact = QLabel(self.lbl_contact_text)
        lbl_contact.setProperty("role", "body")
        self.txt_contact = QLineEdit()
        self.txt_contact.setPlaceholderText(self.placeholder_contact_text)
        self.txt_contact.setFixedHeight(32)

        lbl_desc = QLabel(self.lbl_desc_text)
        lbl_desc.setProperty("role", "body")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.placeholder_desc_text)
        self.txt_desc.setFixedHeight(60)

        lbl_traceback = QLabel(self.lbl_traceback_text)
        lbl_traceback.setProperty("role", "body")
        self.txt_traceback = QTextEdit()
        self.txt_traceback.setReadOnly(True)
        self.txt_traceback.setPlainText(self.traceback_text)
        self.txt_traceback.setFixedHeight(120)
        self.txt_traceback.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; background: #09090b; border: 1px solid #27272a;")

        self.lbl_error = QLabel()
        self.lbl_error.setProperty("state", "error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        self.content_layout.addWidget(lbl_subtitle)
        self.content_layout.addWidget(lbl_contact)
        self.content_layout.addWidget(self.txt_contact)
        self.content_layout.addWidget(lbl_desc)
        self.content_layout.addWidget(self.txt_desc)
        self.content_layout.addWidget(lbl_traceback)
        self.content_layout.addWidget(self.txt_traceback)
        self.content_layout.addWidget(self.lbl_error)

        self.btn_cancel = QPushButton(self.btn_close_text)
        self.btn_cancel.setProperty("role", "action_outlined")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_send = QPushButton(self.btn_send_text)
        self.btn_send.setProperty("role", "action_danger")
        self.btn_send.setFixedHeight(36)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._send_and_close)

        self.add_action_buttons(self.btn_cancel, self.btn_send)

    @Slot()
    def _send_and_close(self):
        if not DISCORD_WEBHOOK_URL:
            self.lbl_error.setText(self.err_no_webhook_text)
            self.lbl_error.show()
            return

        self.btn_send.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        try:
            contact = self.txt_contact.text().strip() or self._get_text("crash.anonymous", "Anónimo")
            desc = self.txt_desc.toPlainText().strip() or self._get_text("crash.no_comments", "Sin comentarios del usuario.")
            
            truncated_tb = self.traceback_text
            if len(truncated_tb) > 1500:
                truncated_tb = truncated_tb[-1500:] + self._get_text("crash.truncated_tb", "\n[Traceback truncado por longitud]")

            content = (
                f"🚨 **CRASH REPORT / REPORTE DE FALLO CRÍTICO** 🚨\n"
                f"**Usuario/Discord:** {contact}\n"
                f"**Versión de MiniKick:** {APP_VERSION}\n"
                f"**¿Qué hacía el usuario?:** {desc}\n"
                f"----------------------------------------\n"
                f"**Traceback:**\n```python\n{truncated_tb}\n```\n"
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
                except Exception:
                    pass

            if files:
                resp = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files, timeout=15)
            else:
                resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)

            if resp.status_code in (200, 204):
                self.accept()
            else:
                raise Exception(f"Discord responded with status code {resp.status_code}")
                
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.lbl_error.setText(self.err_send_text.replace("{error}", str(e)))
            self.lbl_error.show()
            self.btn_send.setEnabled(True)
            self.btn_cancel.setEnabled(True)
            return

        QApplication.restoreOverrideCursor()
