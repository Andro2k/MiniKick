# frontend/controllers/settings_controller.py

from PySide6.QtCore import QObject, Signal, Slot

class SettingsController(QObject):
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
        self.view.minimize_tray_toggled.connect(self.service.set_minimize_tray_enabled)
        self.view.export_clicked.connect(self.handle_export)
        self.view.import_clicked.connect(self.handle_import)
        self.view.unlink_clicked.connect(self.unlink_account_requested.emit)
        self.view.update_clicked.connect(self.check_update_requested.emit)
        self.view.language_changed.connect(self.handle_language_change)

    def _load_initial_state(self):
        enabled = self.service.is_minimize_tray_enabled()
        self.view.set_minimize_tray_enabled(enabled)
        lang = self.service.get_language()
        self.view.set_current_language(lang)

    @Slot()
    def handle_export(self):
        filepath = self.view.ask_save_path()
        if filepath:
            if self.service.export_settings(filepath):
                self.notification_requested.emit(self.view.i18n.get("main.controllers.settings.export_success_title"), self.view.i18n.get("main.controllers.settings.export_success_desc"))
            else:
                self.notification_requested.emit(self.view.i18n.get("main.controllers.settings.error_title"), self.view.i18n.get("main.controllers.settings.export_error_desc"))

    @Slot()
    def handle_import(self):
        filepath = self.view.ask_open_path()
        if filepath:
            if self.service.import_settings(filepath):
                self.backup_restored.emit()
                self.notification_requested.emit(self.view.i18n.get("main.controllers.settings.import_success_title"), self.view.i18n.get("main.controllers.settings.import_success_desc"))
            else:
                self.notification_requested.emit(self.view.i18n.get("main.controllers.settings.error_title"), self.view.i18n.get("main.controllers.settings.import_error_desc"))

    @Slot(str)
    def handle_language_change(self, lang_code: str):
        self.service.set_language(lang_code)
        self.notification_requested.emit(self.view.i18n.get("main.controllers.settings.restart_title"), self.view.i18n.get("main.controllers.settings.restart_desc"))