# backend\controllers\settings_controller.py

import logging
from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger("minikick.controllers.settings")

class SettingsController(QObject):
    style_reload_requested = Signal(int)
    unlink_account_requested = Signal()
    check_update_requested = Signal()
    backup_restored = Signal()
    notification_requested = Signal(str, str)

    def __init__(self, view, service, toast_manager=None, music_provider=None, tts_manager=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.music_provider = music_provider
        self.tts_manager = tts_manager
        if self.view is not None:
            self._connect_signals()
            self._load_initial_state()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
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
        self.view.music_audio_device_changed.connect(self.handle_music_audio_device)
        self.view.tts_audio_device_changed.connect(self.handle_tts_audio_device)
        self.view.feedback_clicked.connect(self.handle_feedback)
        self.view.release_notes_clicked.connect(self.handle_release_notes)

    def _load_initial_state(self):
        enabled = self.service.is_minimize_tray_enabled()
        lang = self.service.get_language()
        current_font = self.service.get_font_size()
        music_device = self.service.get_music_audio_device()
        tts_device = self.service.get_tts_audio_device()

        if self.view is not None:
            self.view.set_minimize_tray_enabled(enabled)
            self.view.set_current_language(lang)
            self.view.set_current_font_size(current_font)
            self.view.set_current_music_audio_device(music_device)
            self.view.set_current_tts_audio_device(tts_device)

        if hasattr(self, 'music_provider') and self.music_provider and hasattr(self.music_provider, 'set_audio_device'):
            self.music_provider.set_audio_device(music_device)
        if hasattr(self, 'tts_manager') and self.tts_manager and hasattr(self.tts_manager, 'set_audio_device'):
            self.tts_manager.set_audio_device(tts_device)

    @Slot(str)
    def handle_music_audio_device(self, device_id: str):
        logger.info("[User Action] Changed music output audio device to: '%s'", device_id)
        self.service.set_music_audio_device(device_id)
        if hasattr(self, 'music_provider') and self.music_provider and hasattr(self.music_provider, 'set_audio_device'):
            self.music_provider.set_audio_device(device_id)

    @Slot(str)
    def handle_tts_audio_device(self, device_id: str):
        logger.info("[User Action] Changed TTS output audio device to: '%s'", device_id)
        self.service.set_tts_audio_device(device_id)
        if hasattr(self, 'tts_manager') and self.tts_manager and hasattr(self.tts_manager, 'set_audio_device'):
            self.tts_manager.set_audio_device(device_id)

    @Slot(bool)
    def handle_minimize_tray(self, enabled: bool):
        logger.info("[User Action] Toggled minimize to tray setting: enabled=%s", enabled)
        self.service.set_minimize_tray_enabled(enabled)
        if self.toast:
            title_key = "settings.status.tray_enabled" if enabled else "settings.status.tray_disabled"
            msg_key = "settings.status.tray_enabled_msg" if enabled else "settings.status.tray_disabled_msg"
            state_color = "success" if enabled else "info"

            self.toast.show_toast(
                title=self.view.i18n.get(title_key),
                message=self.view.i18n.get(msg_key),
                state=state_color
            )

    @Slot()
    def handle_export(self):
        filepath = self.view.ask_save_path()
        if filepath:
            logger.info("[User Action] Exported app settings to: '%s'", filepath)
            if self.service.export_settings(filepath):
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("settings.status.exported"),
                        message=self.view.i18n.get("settings.status.exported_msg"),
                        state="success"
                    )
            else:
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("settings.status.error_title"),
                        message=self.view.i18n.get("settings.status.export_error"),
                        state="danger"
                    )

    @Slot()
    def handle_import(self):
        filepath = self.view.ask_open_path()
        if filepath:
            logger.info("[User Action] Imported app settings from: '%s'", filepath)
            if self.service.import_settings(filepath):
                self.backup_restored.emit()
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("settings.status.imported"),
                        message=self.view.i18n.get("settings.status.imported_msg"),
                        state="success"
                    )
            else:
                if self.toast:
                    self.toast.show_toast(
                        title=self.view.i18n.get("settings.status.error_title"),
                        message=self.view.i18n.get("settings.status.import_error"),
                        state="danger"
                    )

    @Slot(str)
    def handle_language_change(self, lang_code: str):
        logger.info("[User Action] Changed app language to: '%s'", lang_code)
        self.service.set_language(lang_code)
        
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get("settings.status.lang_changed"),
                message=self.view.i18n.get("settings.status.lang_changed_msg"),
                state="info"
            )
            
        self.notification_requested.emit(
            self.view.i18n.get("settings.status.lang_changed"), 
            self.view.i18n.get("settings.status.lang_changed_msg")
        )

    @Slot(int)
    def handle_font_size(self, size: int):
        if size is None:
            return
        logger.info("[User Action] Changed UI font size to: %d", size)
        self.service.set_font_size(size)
        self.style_reload_requested.emit(size)
        
        if self.toast:
            title = self.view.i18n.get("settings.status.font_size_changed")
            msg = self.view.i18n.get("settings.status.font_size_changed_msg").replace("{size}", str(size))
            self.toast.show_toast(title, msg, "success")

    @Slot()
    def handle_feedback(self):
        logger.info("[User Action] Opened Bug Report modal")
        from backend.workers import BugReportWorker
        self.view.show_bug_report_dialog(worker_class=BugReportWorker)

    @Slot()
    def handle_release_notes(self):
        logger.info("[User Action] Opened Release Notes modal")
        from backend.workers import ReleaseNotesWorker
        self.view.show_release_notes_dialog(worker_class=ReleaseNotesWorker)
