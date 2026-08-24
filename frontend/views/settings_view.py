# frontend\views\settings_view.py

from datetime import datetime
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from frontend.widgets import BaseView, SettingRow, ModernCard, ModernButton, ModernSwitch, NoWheelComboBox

class SettingsView(BaseView):
    font_size_changed = Signal(int)
    minimize_tray_toggled = Signal(bool)
    export_clicked = Signal()
    import_clicked = Signal()
    unlink_clicked = Signal()
    update_clicked = Signal()
    release_notes_clicked = Signal()
    language_changed = Signal(str)
    music_audio_device_changed = Signal(str)
    tts_audio_device_changed = Signal(str)
    feedback_clicked = Signal()
    kick_integration_clicked = Signal()
    twitch_integration_clicked = Signal()
    youtube_integration_clicked = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="settings.header.title", subtitle_key="settings.header.subtitle", parent=parent)
        self._setup_ui()

    def _setup_ui(self):
        app_card = ModernCard(parent=self)

        self.combo_lang = NoWheelComboBox(self)
        self.combo_lang.addItem("Español", "es")
        self.combo_lang.addItem("English", "en")
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)

        row_lang = SettingRow(
            icon_name="world.svg", 
            title_text=self.i18n.get("settings.system.lang_title"), 
            desc_text=self.i18n.get("settings.system.lang_desc"), 
            right_widget=self.combo_lang
        )

        self.combo_font = NoWheelComboBox(self)
        font_sizes = [
            (self.i18n.get("settings.system.font_size_small"), 11),
            (self.i18n.get("settings.system.font_size_normal"), 13),
            (self.i18n.get("settings.system.font_size_large"), 14),
            (self.i18n.get("settings.system.font_size_xlarge"), 16)
        ]
        for name, size in font_sizes:
            self.combo_font.addItem(name, size)
        self.combo_font.currentIndexChanged.connect(self._on_font_changed)

        row_font = SettingRow(
            icon_name="file-text.svg", 
            title_text=self.i18n.get("settings.system.font_title"), 
            desc_text=self.i18n.get("settings.system.font_desc"), 
            right_widget=self.combo_font
        )

        self.sw_start_bg = ModernSwitch(self)
        self.sw_start_bg.toggled.connect(self.minimize_tray_toggled.emit)

        row_tray = SettingRow(
            icon_name="minimize.svg", 
            title_text=self.i18n.get("settings.system.tray_title"), 
            desc_text=self.i18n.get("settings.system.tray_desc"), 
            right_widget=self.sw_start_bg
        )

        self.combo_music_audio_device = NoWheelComboBox(self)
        self.combo_music_audio_device.setMinimumWidth(160)
        self.combo_tts_audio_device = NoWheelComboBox(self)
        self.combo_tts_audio_device.setMinimumWidth(160)

        try:
            from PySide6.QtMultimedia import QMediaDevices
            self._media_devices = QMediaDevices(self)
            self._media_devices.audioOutputsChanged.connect(self.populate_audio_devices)
        except Exception as dev_err:
            import logging
            logging.error("[SettingsView] Error connecting audioOutputsChanged: %s", dev_err)

        self.populate_audio_devices()

        self.combo_music_audio_device.currentIndexChanged.connect(self._on_music_audio_device_changed)
        self.combo_tts_audio_device.currentIndexChanged.connect(self._on_tts_audio_device_changed)

        row_music_audio = SettingRow(
            icon_name="music.svg",
            title_text=self.i18n.get("settings.audio.music_title"),
            desc_text=self.i18n.get("settings.audio.music_desc"),
            right_widget=self.combo_music_audio_device
        )

        row_tts_audio = SettingRow(
            icon_name="volume.svg",
            title_text=self.i18n.get("settings.audio.tts_title"),
            desc_text=self.i18n.get("settings.audio.tts_desc"),
            right_widget=self.combo_tts_audio_device
        )

        btn_backup_container = QWidget()
        btn_backup_layout = QHBoxLayout(btn_backup_container)
        btn_backup_layout.setContentsMargins(0, 0, 0, 0) 
        btn_backup_layout.setSpacing(8)
        
        self.btn_export = ModernButton(self.i18n.get("common.buttons.export"), role="action_neutral_border")
        self.btn_import = ModernButton(self.i18n.get("common.buttons.import"), role="action_neutral_border")
        
        self.btn_export.clicked.connect(self.export_clicked.emit)
        self.btn_import.clicked.connect(self.import_clicked.emit)

        btn_backup_layout.addWidget(self.btn_export)
        btn_backup_layout.addWidget(self.btn_import)

        row_backup = SettingRow(
            icon_name="restore.svg", 
            title_text=self.i18n.get("settings.backup.title"), 
            desc_text=self.i18n.get("settings.backup.desc"), 
            right_widget=btn_backup_container
        )

        app_card.addWidget(row_lang)
        app_card.addWidget(row_font)
        app_card.addWidget(row_tray)
        app_card.addWidget(row_music_audio)
        app_card.addWidget(row_tts_audio)
        app_card.addWidget(row_backup)
        self.main_layout.addWidget(app_card)

        integrations_card = ModernCard(parent=self)

        self.btn_kick_integration = ModernButton(self.i18n.get("settings.integrations.btn_connect_kick"), role="action_accent", parent=self)
        self.btn_kick_integration.clicked.connect(self.unlink_clicked.emit)
        self.btn_unlink = self.btn_kick_integration

        self.row_kick_integration = SettingRow(
            icon_name="brand-kick.svg",
            title_text=self.i18n.get("settings.integrations.kick_title"),
            desc_text=self.i18n.get("settings.integrations.desc"),
            right_widget=self.btn_kick_integration
        )

        self.btn_twitch_integration = ModernButton(self.i18n.get("settings.integrations.btn_connect_twitch"), role="action_accent", parent=self)
        self.btn_twitch_integration.clicked.connect(self.twitch_integration_clicked.emit)

        self.row_twitch_integration = SettingRow(
            icon_name="brand-twitch.svg",
            title_text=self.i18n.get("settings.integrations.twitch_title"),
            desc_text=self.i18n.get("settings.integrations.desc"),
            right_widget=self.btn_twitch_integration
        )

        self.btn_youtube_integration = ModernButton(self.i18n.get("settings.integrations.btn_connect_youtube"), role="action_accent", parent=self)
        self.btn_youtube_integration.clicked.connect(self.youtube_integration_clicked.emit)

        self.row_youtube_integration = SettingRow(
            icon_name="brand-youtube.svg",
            title_text=self.i18n.get("settings.integrations.youtube_title"),
            desc_text=self.i18n.get("settings.integrations.desc"),
            right_widget=self.btn_youtube_integration
        )

        integrations_card.addWidget(self.row_kick_integration)
        integrations_card.addWidget(self.row_twitch_integration)
        integrations_card.addWidget(self.row_youtube_integration)
        self.main_layout.addWidget(integrations_card)

        support_card = ModernCard(parent=self)

        self.btn_update = ModernButton(self.i18n.get("common.buttons.update"), role="action_accent")
        self.btn_update.clicked.connect(self.update_clicked.emit)

        row_update = SettingRow(
            icon_name="cloud-download.svg", 
            title_text=self.i18n.get("settings.system.update_title"), 
            desc_text=self.i18n.get("settings.system.update_desc"), 
            right_widget=self.btn_update
        )

        self.btn_release_notes = ModernButton(self.i18n.get("common.buttons.view_release_notes"), role="action_outlined")
        self.btn_release_notes.clicked.connect(self.release_notes_clicked.emit)

        row_release_notes = SettingRow(
            icon_name="file-text.svg",
            title_text=self.i18n.get("settings.system.release_notes_title"),
            desc_text=self.i18n.get("settings.system.release_notes_desc"),
            right_widget=self.btn_release_notes
        )

        self.btn_feedback = ModernButton(self.i18n.get("common.buttons.report_bug"), role="action_accent")
        self.btn_feedback.clicked.connect(self.feedback_clicked.emit)

        row_feedback = SettingRow(
            icon_name="bug.svg", 
            title_text=self.i18n.get("settings.feedback.title"), 
            desc_text=self.i18n.get("settings.feedback.desc"), 
            right_widget=self.btn_feedback
        )

        support_card.addWidget(row_update)
        support_card.addWidget(row_release_notes)
        support_card.addWidget(row_feedback)
        self.main_layout.addWidget(support_card)
        
        self.main_layout.addStretch()

    def set_minimize_tray_enabled(self, enabled: bool):
        self.sw_start_bg.blockSignals(True)
        self.sw_start_bg.setChecked(enabled)
        self.sw_start_bg.blockSignals(False)

    def set_current_font_size(self, size: int):
        self.combo_font.blockSignals(True)
        idx = self.combo_font.findData(size)
        if idx >= 0:
            self.combo_font.setCurrentIndex(idx)
        self.combo_font.blockSignals(False)

    def set_current_language(self, lang_code: str):
        self.combo_lang.blockSignals(True)
        idx = self.combo_lang.findData(lang_code)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.blockSignals(False)

    def ask_save_path(self) -> str:
        default_name = f"MiniKick_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        dialog_title = self.i18n.get("settings.dialogs.export_title")
        filepath, _ = QFileDialog.getSaveFileName(
            self, dialog_title, default_name, "JSON Files (*.json)"
        )
        return filepath

    def ask_open_path(self) -> str:
        dialog_title = self.i18n.get("settings.dialogs.import_title")
        filepath, _ = QFileDialog.getOpenFileName(
            self, dialog_title, "", "JSON Files (*.json)"
        )
        return filepath

    def _on_language_changed(self, index: int):
        lang_code = self.combo_lang.itemData(index)
        self.language_changed.emit(lang_code)

    def _on_font_changed(self, index: int):
        size = self.combo_font.itemData(index)
        self.font_size_changed.emit(size)

    def show_bug_report_dialog(self, worker_class=None) -> None:
        from frontend.dialogs.bug_report_dialog import BugReportDialog
        dialog = BugReportDialog(self.i18n, worker_class=worker_class, parent=self.window())
        dialog.exec()

    def show_release_notes_dialog(self, worker_class=None) -> None:
        from frontend.dialogs.release_notes_dialog import ReleaseNotesDialog
        dialog = ReleaseNotesDialog(self.i18n, worker_class=worker_class, parent=self.window())
        dialog.exec()

    def set_integrations_status(self, kick_connected: bool = False, kick_channel: str = "", twitch_connected: bool = False, twitch_channel: str = "", youtube_connected: bool = False, youtube_channel: str = "") -> None:
        if kick_connected and kick_channel:
            text_kick = self.i18n.get("settings.integrations.btn_disconnect_kick").replace("{channel}", kick_channel)
            desc_kick = self.i18n.get("settings.integrations.kick_desc_connected").replace("{channel}", kick_channel)
            self.btn_kick_integration.setText(text_kick)
            self.btn_kick_integration.setProperty("role", "action_danger_border")
            if hasattr(self, 'row_kick_integration') and self.row_kick_integration:
                self.row_kick_integration.set_description(desc_kick)
        else:
            text_kick = self.i18n.get("settings.integrations.btn_connect_kick")
            desc_kick = self.i18n.get("settings.integrations.kick_desc_disconnected")
            self.btn_kick_integration.setText(text_kick)
            self.btn_kick_integration.setProperty("role", "action_accent")
            if hasattr(self, 'row_kick_integration') and self.row_kick_integration:
                self.row_kick_integration.set_description(desc_kick)

        self.btn_kick_integration.style().unpolish(self.btn_kick_integration)
        self.btn_kick_integration.style().polish(self.btn_kick_integration)

        if twitch_connected and twitch_channel:
            text = self.i18n.get("settings.integrations.btn_disconnect_twitch").replace("{channel}", twitch_channel)
            desc = self.i18n.get("settings.integrations.twitch_desc_connected").replace("{channel}", twitch_channel)
            self.btn_twitch_integration.setText(text)
            self.btn_twitch_integration.setProperty("role", "action_danger_border")
            if hasattr(self, 'row_twitch_integration') and self.row_twitch_integration:
                self.row_twitch_integration.set_description(desc)
        else:
            text = self.i18n.get("settings.integrations.btn_connect_twitch")
            desc = self.i18n.get("settings.integrations.desc")
            self.btn_twitch_integration.setText(text)
            self.btn_twitch_integration.setProperty("role", "action_accent")
            if hasattr(self, 'row_twitch_integration') and self.row_twitch_integration:
                self.row_twitch_integration.set_description(desc)

        self.btn_twitch_integration.style().unpolish(self.btn_twitch_integration)
        self.btn_twitch_integration.style().polish(self.btn_twitch_integration)

        if youtube_connected and youtube_channel:
            short_channel = self._format_target_for_button(youtube_channel)
            text_yt = self.i18n.get("settings.integrations.btn_disconnect_youtube").replace("{channel}", short_channel)
            desc_yt = self.i18n.get("settings.integrations.youtube_desc_connected").replace("{channel}", youtube_channel)
            self.btn_youtube_integration.setText(text_yt)
            self.btn_youtube_integration.setProperty("role", "action_danger_border")
            if hasattr(self, 'row_youtube_integration') and self.row_youtube_integration:
                self.row_youtube_integration.set_description(desc_yt)
        else:
            text_yt = self.i18n.get("settings.integrations.btn_connect_youtube")
            desc_yt = self.i18n.get("settings.integrations.desc")
            self.btn_youtube_integration.setText(text_yt)
            self.btn_youtube_integration.setProperty("role", "action_accent")
            if hasattr(self, 'row_youtube_integration') and self.row_youtube_integration:
                self.row_youtube_integration.set_description(desc_yt)

        self.btn_youtube_integration.style().unpolish(self.btn_youtube_integration)
        self.btn_youtube_integration.style().polish(self.btn_youtube_integration)

    @staticmethod
    def _format_target_for_button(target: str) -> str:
        if not target:
            return ""
        clean = target.strip()
        if "/@" in clean:
            handle = clean.split("/@")[1].split("/")[0].split("?")[0]
            return f"@{handle}"
        if clean.startswith("@"):
            return clean
        import re
        v_match = re.search(r'(?:v=|youtu\.be/|/live/|/embed/)([a-zA-Z0-9_-]{11})', clean)
        if v_match:
            return f"#{v_match.group(1)[:8]}"
        ch_match = re.search(r'/channel/([a-zA-Z0-9_-]+)', clean)
        if ch_match:
            ch_id = ch_match.group(1)
            return f"UC...{ch_id[-4:]}" if len(ch_id) > 8 else ch_id
        if not clean.startswith("http"):
            return f"@{clean}"
        if len(clean) > 16:
            return clean[:14] + "…"
        return clean

    def populate_audio_devices(self):
        curr_music_dev = self.combo_music_audio_device.currentData() if hasattr(self, 'combo_music_audio_device') else "default"
        curr_tts_dev = self.combo_tts_audio_device.currentData() if hasattr(self, 'combo_tts_audio_device') else "default"

        self.combo_music_audio_device.blockSignals(True)
        self.combo_tts_audio_device.blockSignals(True)
        try:
            self.combo_music_audio_device.clear()
            self.combo_tts_audio_device.clear()

            default_text = self.i18n.get("settings.audio.default_device")
            self.combo_music_audio_device.addItem(default_text, "default")
            self.combo_tts_audio_device.addItem(default_text, "default")

            try:
                from PySide6.QtMultimedia import QMediaDevices
                for dev in QMediaDevices.audioOutputs():
                    dev_id = dev.id().data().decode("utf-8", errors="ignore") if hasattr(dev.id(), "data") else str(dev.id())
                    name = dev.description()
                    self.combo_music_audio_device.addItem(name, dev_id)
                    self.combo_tts_audio_device.addItem(name, dev_id)
            except Exception as e:
                import logging
                logging.error("[SettingsView] Error populating audio devices: %s", e)

            if curr_music_dev:
                idx = self.combo_music_audio_device.findData(curr_music_dev)
                if idx >= 0:
                    self.combo_music_audio_device.setCurrentIndex(idx)
            if curr_tts_dev:
                idx = self.combo_tts_audio_device.findData(curr_tts_dev)
                if idx >= 0:
                    self.combo_tts_audio_device.setCurrentIndex(idx)
        finally:
            self.combo_music_audio_device.blockSignals(False)
            self.combo_tts_audio_device.blockSignals(False)

    def set_current_music_audio_device(self, device_id: str):
        self.combo_music_audio_device.blockSignals(True)
        idx = self.combo_music_audio_device.findData(device_id)
        if idx >= 0:
            self.combo_music_audio_device.setCurrentIndex(idx)
        else:
            self.combo_music_audio_device.setCurrentIndex(0)
        self.combo_music_audio_device.blockSignals(False)

    def set_current_tts_audio_device(self, device_id: str):
        self.combo_tts_audio_device.blockSignals(True)
        idx = self.combo_tts_audio_device.findData(device_id)
        if idx >= 0:
            self.combo_tts_audio_device.setCurrentIndex(idx)
        else:
            self.combo_tts_audio_device.setCurrentIndex(0)
        self.combo_tts_audio_device.blockSignals(False)

    def _on_music_audio_device_changed(self, index: int):
        device_id = self.combo_music_audio_device.itemData(index)
        if device_id is not None:
            self.music_audio_device_changed.emit(str(device_id))

    def _on_tts_audio_device_changed(self, index: int):
        device_id = self.combo_tts_audio_device.itemData(index)
        if device_id is not None:
            self.tts_audio_device_changed.emit(str(device_id))
