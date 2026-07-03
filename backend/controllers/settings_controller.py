# frontend\controllers\settings_controller.py

from PySide6.QtCore import QObject, Signal, Slot

class SettingsController(QObject):
    style_reload_requested = Signal(int)
    unlink_account_requested = Signal()
    check_update_requested = Signal()
    backup_restored = Signal()
    notification_requested = Signal(str, str)

    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self._connect_signals()
        self._load_initial_state()

    def _connect_signals(self):
        self.view.font_size_changed.connect(self.handle_font_size)
        self.view.minimize_tray_toggled.connect(self.handle_minimize_tray)
        self.view.export_clicked.connect(self.handle_export)
        self.view.import_clicked.connect(self.handle_import)
        self.view.unlink_clicked.connect(self.unlink_account_requested.emit)
        self.view.update_clicked.connect(self.check_update_requested.emit)
        self.view.language_changed.connect(self.handle_language_change)
        self.view.feedback_clicked.connect(self.handle_feedback)

    def _load_initial_state(self):
        enabled = self.service.is_minimize_tray_enabled()
        self.view.set_minimize_tray_enabled(enabled)
        lang = self.service.get_language()
        self.view.set_current_language(lang)
        current_font = self.service.get_font_size()
        self.view.set_current_font_size(current_font)
        self.style_reload_requested.emit(current_font)

    @Slot(bool)
    def handle_minimize_tray(self, enabled: bool):
        self.service.set_minimize_tray_enabled(enabled)
        
        if hasattr(self.view.window(), 'toast'):
            title_key = "settings.status.tray_enabled" if enabled else "settings.status.tray_disabled"
            fallback_title = "Segundo Plano Activo" if enabled else "Segundo Plano Inactivo"
            msg_key = "settings.status.tray_enabled_msg" if enabled else "settings.status.tray_disabled_msg"
            fallback_msg = "La app se minimizará a la bandeja" if enabled else "La app se cerrará por completo"
            state_color = "success" if enabled else "info"

            self.view.window().toast.show_toast(
                title=self.view.i18n.get(title_key) or fallback_title,
                message=self.view.i18n.get(msg_key) or fallback_msg,
                state=state_color
            )

    @Slot()
    def handle_export(self):
        filepath = self.view.ask_save_path()
        if filepath:
            if self.service.export_settings(filepath):
                if hasattr(self.view.window(), 'toast'):
                    self.view.window().toast.show_toast(
                        title=self.view.i18n.get("settings.status.exported"),
                        message=self.view.i18n.get("settings.status.exported_msg"),
                        state="success"
                    )
            else:
                if hasattr(self.view.window(), 'toast'):
                    self.view.window().toast.show_toast(
                        title=self.view.i18n.get("settings.status.error_title"),
                        message=self.view.i18n.get("settings.status.export_error"),
                        state="danger"
                    )

    @Slot()
    def handle_import(self):
        filepath = self.view.ask_open_path()
        if filepath:
            if self.service.import_settings(filepath):
                self.backup_restored.emit()
                if hasattr(self.view.window(), 'toast'):
                    self.view.window().toast.show_toast(
                        title=self.view.i18n.get("settings.status.imported"),
                        message=self.view.i18n.get("settings.status.imported_msg"),
                        state="success"
                    )
            else:
                if hasattr(self.view.window(), 'toast'):
                    self.view.window().toast.show_toast(
                        title=self.view.i18n.get("settings.status.error_title"),
                        message=self.view.i18n.get("settings.status.import_error"),
                        state="danger"
                    )

    @Slot(str)
    def handle_language_change(self, lang_code: str):
        self.service.set_language(lang_code)
        
        if hasattr(self.view.window(), 'toast'):
            self.view.window().toast.show_toast(
                title=self.view.i18n.get("settings.status.lang_changed"),
                message=self.view.i18n.get("settings.status.lang_changed_msg"),
                state="info"
            )
            
        self.notification_requested.emit(
            self.view.i18n.get("main.controllers.settings.restart_title"), 
            self.view.i18n.get("main.controllers.settings.restart_desc")
        )

    @Slot(int)
    def handle_font_size(self, size: int):
        self.service.set_font_size(size)
        self.style_reload_requested.emit(size)
        
        if hasattr(self.view.window(), 'toast'):
            title = self.view.i18n.get("settings.status.font_size_changed")
            msg = self.view.i18n.get("settings.status.font_size_changed_msg").replace("{size}", str(size))
            self.view.window().toast.show_toast(title, msg, "success")

    @Slot()
    def handle_feedback(self):
        from frontend.dialogs.bug_report_dialog import BugReportDialog
        dialog = BugReportDialog(self.view.i18n, parent=self.view.window())
        dialog.exec()