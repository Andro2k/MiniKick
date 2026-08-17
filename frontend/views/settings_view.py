# frontend\views\settings_view.py

from datetime import datetime
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from frontend.common.utils import NoWheelComboBox
from frontend.common.theme import COLOR_RED
from frontend.widgets import BaseView, SettingRow, ModernCard, ModernButton, ModernSwitch

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

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="settings.header.title", subtitle_key="settings.header.subtitle", parent=parent)
        self._setup_ui()

    def _setup_ui(self):
        sys_card = ModernCard(parent=self)

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

        sys_card.addWidget(row_lang)
        sys_card.addWidget(row_font)
        sys_card.addWidget(row_tray)        
        sys_card.addWidget(row_update)
        sys_card.addWidget(row_release_notes)
        self.main_layout.addWidget(sys_card)

        audio_card = ModernCard(parent=self)

        self.combo_music_audio_device = NoWheelComboBox(self)
        self.combo_tts_audio_device = NoWheelComboBox(self)

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

        audio_card.addWidget(row_music_audio)
        audio_card.addWidget(row_tts_audio)
        self.main_layout.addWidget(audio_card)

        integrations_card = ModernCard(parent=self)

        self.btn_twitch_integration = ModernButton(self.i18n.get("settings.integrations.btn_connect_twitch"), role="action_accent", parent=self)
        self.btn_twitch_integration.clicked.connect(self.twitch_integration_clicked.emit)

        self.row_twitch_integration = SettingRow(
            icon_name="twitch.svg",
            title_text=self.i18n.get("settings.integrations.twitch_title"),
            desc_text=self.i18n.get("settings.integrations.desc"),
            right_widget=self.btn_twitch_integration
        )

        integrations_card.addWidget(self.row_twitch_integration)
        self.main_layout.addWidget(integrations_card)

        backup_card = ModernCard(parent=self)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0) 
        btn_layout.setSpacing(8)
        
        self.btn_export = ModernButton(self.i18n.get("common.buttons.export"), role="action_neutral_border")
        self.btn_import = ModernButton(self.i18n.get("common.buttons.import"), role="action_neutral_border")
        
        self.btn_export.clicked.connect(self.export_clicked.emit)
        self.btn_import.clicked.connect(self.import_clicked.emit)

        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_import)

        row_backup = SettingRow(
            icon_name="restore.svg", 
            title_text=self.i18n.get("settings.backup.title"), 
            desc_text=self.i18n.get("settings.backup.desc"), 
            right_widget=btn_container
        )

        backup_card.addWidget(row_backup)
        self.main_layout.addWidget(backup_card)

        account_card = ModernCard(parent=self)

        self.btn_unlink = ModernButton(self.i18n.get("common.buttons.unlink"), role="action_danger_border")
        self.btn_unlink.clicked.connect(self.unlink_clicked.emit)
        
        row_unlink = SettingRow(
            icon_name="user-x.svg", 
            title_text=self.i18n.get("settings.account.title"), 
            desc_text=self.i18n.get("settings.account.desc"), 
            right_widget=self.btn_unlink,
            title_color=COLOR_RED,
            icon_color=COLOR_RED
        )

        account_card.addWidget(row_unlink)
        self.main_layout.addWidget(account_card)

        feedback_card = ModernCard(parent=self)

        self.btn_feedback = ModernButton(self.i18n.get("common.buttons.report_bug"), role="action_accent")
        self.btn_feedback.clicked.connect(self.feedback_clicked.emit)

        row_feedback = SettingRow(
            icon_name="bug.svg", 
            title_text=self.i18n.get("settings.feedback.title"), 
            desc_text=self.i18n.get("settings.feedback.desc"), 
            right_widget=self.btn_feedback
        )

        feedback_card.addWidget(row_feedback)
        self.main_layout.addWidget(feedback_card)
        
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

    def show_bug_report_dialog(self) -> None:
        from frontend.dialogs.bug_report_dialog import BugReportDialog
        dialog = BugReportDialog(self.i18n, parent=self.window())
        dialog.exec()

    def show_release_notes_dialog(self) -> None:
        from frontend.dialogs.release_notes_dialog import ReleaseNotesDialog
        dialog = ReleaseNotesDialog(self.i18n, parent=self.window())
        dialog.exec()

    def set_integrations_status(self, kick_connected: bool = False, kick_channel: str = "", twitch_connected: bool = False, twitch_channel: str = "") -> None:
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
