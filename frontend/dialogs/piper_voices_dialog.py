# frontend\dialogs\piper_voices_dialog.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSize, Signal, Slot
from frontend.dialogs.base_dialog import ModernFramelessShell
from frontend.widgets import NoWheelDoubleSpinBox
from frontend.common import get_icon_colored, get_pixmap_colored
from frontend.common.theme import COLOR_NEUTRAL_200, COLOR_GREEN
from backend.services.chat.piper_voice_manager import (
    PiperVoiceManager, PiperVoiceDownloadWorker, DEFAULT_PIPER_VOICE_ID
)

class PiperVoiceItemWidget(QFrame):
    download_requested = Signal(str)
    delete_requested = Signal(str)
    test_requested = Signal(str)

    def __init__(self, voice_meta: dict, is_installed: bool, i18n, parent=None):
        super().__init__(parent)
        self.voice_meta = voice_meta
        self.voice_id = voice_meta["id"]
        self.is_installed = is_installed
        self.i18n = i18n
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lang_str = self.voice_meta.get("lang", "es_ES")
        badge_lbl = QLabel(lang_str.upper(), self)
        badge_lbl.setProperty("role", "code")
        badge_lbl.setFixedWidth(54)
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.lbl_name = QLabel(self.voice_meta.get("name", self.voice_id), self)
        self.lbl_name.setProperty("role", "body")
        self.lbl_name.setProperty("state", "bold")

        size_text = self.voice_meta.get("size_mb", "")
        quality_text = self.voice_meta.get("quality", "medium")
        self.lbl_sub = QLabel(f"{size_text} • {quality_text.capitalize()}", self)
        self.lbl_sub.setProperty("role", "caption")

        info_layout.addWidget(self.lbl_name)
        info_layout.addWidget(self.lbl_sub)

        header_layout.addWidget(badge_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addLayout(info_layout, stretch=1)

        self.lbl_status = QLabel(self)
        self.lbl_status.setProperty("role", "caption")
        self.update_status(self.is_installed)
        header_layout.addWidget(self.lbl_status, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.btn_test = QPushButton(self)
        self.btn_test.setIcon(get_icon_colored("volume.svg", COLOR_NEUTRAL_200, size=14))
        self.btn_test.setIconSize(QSize(14, 14))
        self.btn_test.setFixedSize(28, 28)
        self.btn_test.setProperty("role", "action_neutral_border")
        self.btn_test.setToolTip(self.i18n.get("chat.status.test_btn_tooltip"))
        self.btn_test.clicked.connect(lambda: self.test_requested.emit(self.voice_id))
        self.btn_test.setVisible(self.is_installed)
        header_layout.addWidget(self.btn_test)

        self.btn_action = QPushButton(self)
        self.btn_action.setFixedHeight(28)
        self.btn_action.clicked.connect(self._on_action_clicked)
        self._update_action_button()
        header_layout.addWidget(self.btn_action)

        main_layout.addLayout(header_layout)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _update_action_button(self):
        if self.is_installed:
            self.btn_action.setText(self.i18n.get("piper_dialog.btn_delete"))
            self.btn_action.setProperty("role", "action_danger_border")
            self.btn_action.setEnabled(self.voice_id != DEFAULT_PIPER_VOICE_ID)
        else:
            self.btn_action.setText(self.i18n.get("piper_dialog.btn_download"))
            self.btn_action.setProperty("role", "action_accent")
            self.btn_action.setEnabled(True)
        self.btn_action.style().unpolish(self.btn_action)
        self.btn_action.style().polish(self.btn_action)

    def update_status(self, is_installed: bool):
        self.is_installed = is_installed
        if is_installed:
            self.lbl_status.setText(self.i18n.get("piper_dialog.status_installed"))
            self.lbl_status.setProperty("state", "success")
        else:
            self.lbl_status.setText(self.i18n.get("piper_dialog.status_not_installed"))
            self.lbl_status.setProperty("state", "neutral")
        self.lbl_status.style().unpolish(self.lbl_status)
        self.lbl_status.style().polish(self.lbl_status)
        if hasattr(self, "btn_test"):
            self.btn_test.setVisible(is_installed)
        if hasattr(self, "btn_action"):
            self._update_action_button()

    def set_downloading(self, downloading: bool, percent: int = 0):
        self.progress_bar.setVisible(downloading)
        self.progress_bar.setValue(percent)
        self.btn_action.setEnabled(not downloading)
        if downloading:
            self.btn_action.setText(f"{percent}%")
            self.lbl_status.setText(self.i18n.get("piper_dialog.status_downloading"))
            self.lbl_status.setProperty("state", "info")
            self.lbl_status.style().unpolish(self.lbl_status)
            self.lbl_status.style().polish(self.lbl_status)

    def _on_action_clicked(self):
        if self.is_installed:
            self.delete_requested.emit(self.voice_id)
        else:
            self.download_requested.emit(self.voice_id)

class PiperVoicesDialog(ModernFramelessShell):
    voices_updated = Signal()

    def __init__(self, i18n, tts_service, parent=None):
        super().__init__(width=660, parent=parent)
        self.i18n = i18n
        self.tts_service = tts_service
        self.manager = PiperVoiceManager()
        self._active_workers: dict[str, PiperVoiceDownloadWorker] = {}
        self._item_widgets: dict[str, PiperVoiceItemWidget] = {}
        self._setup_ui()
        self._load_synthesis_params()

    def _setup_ui(self):
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(get_pixmap_colored("microphone.svg", COLOR_GREEN, size=24))
        header_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        lbl_title = QLabel(self.i18n.get("piper_dialog.title"), self)
        lbl_title.setProperty("role", "h2")

        lbl_subtitle = QLabel(self.i18n.get("piper_dialog.subtitle"), self)
        lbl_subtitle.setProperty("role", "caption")
        lbl_subtitle.setWordWrap(True)

        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_subtitle)
        header_layout.addLayout(title_layout, stretch=1)
        header_layout.addSpacing(28)

        layout.addLayout(header_layout)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(390)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(2, 2, 8, 2)
        self.scroll_layout.setSpacing(8)

        self._populate_catalog()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        synthesis_card = QFrame(self)
        synthesis_card.setProperty("role", "card")
        card_layout = QVBoxLayout(synthesis_card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)

        card_header = QHBoxLayout()
        card_title_layout = QVBoxLayout()
        card_title_layout.setSpacing(2)

        lbl_syn_title = QLabel(self.i18n.get("piper_dialog.synthesis_title"), synthesis_card)
        lbl_syn_title.setProperty("role", "body")
        lbl_syn_title.setProperty("state", "bold")

        lbl_syn_desc = QLabel(self.i18n.get("piper_dialog.synthesis_desc"), synthesis_card)
        lbl_syn_desc.setProperty("role", "caption")

        card_title_layout.addWidget(lbl_syn_title)
        card_title_layout.addWidget(lbl_syn_desc)
        card_header.addLayout(card_title_layout, stretch=1)

        self.btn_reset_synthesis = QPushButton(self.i18n.get("piper_dialog.btn_reset_synthesis"), synthesis_card)
        self.btn_reset_synthesis.setProperty("role", "action_neutral_border")
        self.btn_reset_synthesis.setToolTip(self.i18n.get("piper_dialog.btn_reset_tooltip"))
        self.btn_reset_synthesis.setFixedHeight(26)
        self.btn_reset_synthesis.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_synthesis.clicked.connect(self._reset_synthesis_defaults)
        card_header.addWidget(self.btn_reset_synthesis)

        card_layout.addLayout(card_header)

        params_layout = QHBoxLayout()
        params_layout.setSpacing(12)

        col_length = QVBoxLayout()
        col_length.setSpacing(3)
        lbl_length = QLabel(self.i18n.get("piper_dialog.param_length_scale"), synthesis_card)
        lbl_length.setProperty("role", "caption")
        lbl_length.setToolTip(self.i18n.get("piper_dialog.param_length_scale_desc"))
        self.spin_length = NoWheelDoubleSpinBox(synthesis_card)
        self.spin_length.setRange(0.20, 3.00)
        self.spin_length.setSingleStep(0.05)
        self.spin_length.setDecimals(2)
        self.spin_length.setToolTip(self.i18n.get("piper_dialog.param_length_scale_desc"))
        self.spin_length.valueChanged.connect(self._on_synthesis_params_changed)
        col_length.addWidget(lbl_length)
        col_length.addWidget(self.spin_length)
        params_layout.addLayout(col_length)

        col_noise = QVBoxLayout()
        col_noise.setSpacing(3)
        lbl_noise = QLabel(self.i18n.get("piper_dialog.param_noise_scale"), synthesis_card)
        lbl_noise.setProperty("role", "caption")
        lbl_noise.setToolTip(self.i18n.get("piper_dialog.param_noise_scale_desc"))
        self.spin_noise = NoWheelDoubleSpinBox(synthesis_card)
        self.spin_noise.setRange(0.00, 2.00)
        self.spin_noise.setSingleStep(0.05)
        self.spin_noise.setDecimals(2)
        self.spin_noise.setToolTip(self.i18n.get("piper_dialog.param_noise_scale_desc"))
        self.spin_noise.valueChanged.connect(self._on_synthesis_params_changed)
        col_noise.addWidget(lbl_noise)
        col_noise.addWidget(self.spin_noise)
        params_layout.addLayout(col_noise)

        col_noise_w = QVBoxLayout()
        col_noise_w.setSpacing(3)
        lbl_noise_w = QLabel(self.i18n.get("piper_dialog.param_noise_w_scale"), synthesis_card)
        lbl_noise_w.setProperty("role", "caption")
        lbl_noise_w.setToolTip(self.i18n.get("piper_dialog.param_noise_w_scale_desc"))
        self.spin_noise_w = NoWheelDoubleSpinBox(synthesis_card)
        self.spin_noise_w.setRange(0.00, 2.00)
        self.spin_noise_w.setSingleStep(0.05)
        self.spin_noise_w.setDecimals(2)
        self.spin_noise_w.setToolTip(self.i18n.get("piper_dialog.param_noise_w_scale_desc"))
        self.spin_noise_w.valueChanged.connect(self._on_synthesis_params_changed)
        col_noise_w.addWidget(lbl_noise_w)
        col_noise_w.addWidget(self.spin_noise_w)
        params_layout.addLayout(col_noise_w)

        card_layout.addLayout(params_layout)
        layout.addWidget(synthesis_card)

        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton(self.i18n.get("piper_dialog.btn_import"), self)
        self.btn_import.setProperty("role", "action_neutral_border")
        self.btn_import.setToolTip(self.i18n.get("piper_dialog.btn_import_tooltip"))
        self.btn_import.setIcon(get_icon_colored("cloud-download.svg", COLOR_NEUTRAL_200, size=14))
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import.clicked.connect(self._on_import_model_clicked)
        btn_layout.addWidget(self.btn_import)

        btn_layout.addStretch()

        btn_close = QPushButton(self.i18n.get("piper_dialog.btn_close"), self)
        btn_close.setProperty("role", "action_accent")
        btn_close.setFixedWidth(120)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _load_synthesis_params(self):
        ls, ns, nws = 1.0, 0.667, 0.8
        if hasattr(self.tts_service, "get_settings"):
            settings = self.tts_service.get_settings()
            ls = float(settings.get("piper_length_scale", 1.0))
            ns = float(settings.get("piper_noise_scale", 0.667))
            nws = float(settings.get("piper_noise_w_scale", 0.8))
        elif hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "get_piper_synthesis_params"):
            ls, ns, nws = self.tts_service.tts.get_piper_synthesis_params()

        self.spin_length.blockSignals(True)
        self.spin_noise.blockSignals(True)
        self.spin_noise_w.blockSignals(True)

        self.spin_length.setValue(ls)
        self.spin_noise.setValue(ns)
        self.spin_noise_w.setValue(nws)

        self.spin_length.blockSignals(False)
        self.spin_noise.blockSignals(False)
        self.spin_noise_w.blockSignals(False)

    def _on_synthesis_params_changed(self):
        ls = self.spin_length.value()
        ns = self.spin_noise.value()
        nws = self.spin_noise_w.value()
        if hasattr(self.tts_service, "set_piper_synthesis_params"):
            self.tts_service.set_piper_synthesis_params(ls, ns, nws)
        elif hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "set_piper_synthesis_params"):
            self.tts_service.tts.set_piper_synthesis_params(ls, ns, nws)

    def _reset_synthesis_defaults(self):
        self.spin_length.setValue(1.00)
        self.spin_noise.setValue(0.67)
        self.spin_noise_w.setValue(0.80)
        self._on_synthesis_params_changed()

    def _populate_catalog(self):
        catalog = self.manager.get_catalog()
        catalog_ids = set()
        for meta in catalog:
            voice_id = meta["id"]
            catalog_ids.add(voice_id)
            is_inst = self.manager.is_voice_installed(voice_id)
            item = PiperVoiceItemWidget(meta, is_inst, self.i18n, parent=self)
            item.download_requested.connect(self._start_download)
            item.delete_requested.connect(self._delete_voice)
            item.test_requested.connect(self._test_voice)
            self._item_widgets[voice_id] = item
            self.scroll_layout.addWidget(item)

        installed_all = self.manager.get_installed_voices()
        for inst_meta in installed_all:
            vid = inst_meta["id"]
            if vid not in catalog_ids:
                meta = {
                    "id": vid,
                    "name": inst_meta["name"],
                    "lang": inst_meta.get("lang", "es"),
                    "quality": inst_meta.get("quality", "custom"),
                    "size_mb": "Local"
                }
                item = PiperVoiceItemWidget(meta, True, self.i18n, parent=self)
                item.delete_requested.connect(self._delete_voice)
                item.test_requested.connect(self._test_voice)
                self._item_widgets[vid] = item
                self.scroll_layout.addWidget(item)

        self.scroll_layout.addStretch()

    def _refresh_catalog(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._item_widgets.clear()
        self._populate_catalog()

    def _on_import_model_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.get("piper_dialog.import_title"),
            "",
            self.i18n.get("piper_dialog.import_filter")
        )
        if not file_path:
            return
        
        json_path = file_path + ".json"
        if not os.path.exists(json_path):
            json_alt = os.path.splitext(file_path)[0] + ".json"
            if os.path.exists(json_alt):
                json_path = json_alt
            else:
                QMessageBox.warning(self, self.i18n.get("piper_dialog.title"), self.i18n.get("piper_dialog.import_missing_json"))
                return
        
        imported = self.manager.import_local_voice(file_path, json_path)
        if imported:
            if hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "invalidate_voices_cache"):
                self.tts_service.tts.invalidate_voices_cache("piper")
            self.voices_updated.emit()
            self._refresh_catalog()

    @Slot(str)
    def _start_download(self, voice_id: str):
        if voice_id in self._active_workers:
            return

        item = self._item_widgets.get(voice_id)
        if item:
            item.set_downloading(True, 0)

        worker = PiperVoiceDownloadWorker(voice_id, self.manager, parent=self)
        worker.progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_download_finished)
        self._active_workers[voice_id] = worker
        worker.start()

    @Slot(str, int, float, float)
    def _on_download_progress(self, voice_id: str, percent: int, down_mb: float, tot_mb: float):
        item = self._item_widgets.get(voice_id)
        if item:
            item.set_downloading(True, percent)

    @Slot(str, bool, str)
    def _on_download_finished(self, voice_id: str, success: bool, err_msg: str):
        if voice_id in self._active_workers:
            worker = self._active_workers.pop(voice_id)
            worker.deleteLater()

        item = self._item_widgets.get(voice_id)
        if item:
            item.set_downloading(False)
            item.update_status(success)

        if success:
            if hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "invalidate_voices_cache"):
                self.tts_service.tts.invalidate_voices_cache("piper")
            self.voices_updated.emit()

    @Slot(str)
    def _delete_voice(self, voice_id: str):
        ok = self.manager.delete_voice(voice_id)
        item = self._item_widgets.get(voice_id)
        if item:
            item.update_status(not ok)
        if ok:
            if hasattr(self.tts_service, "tts") and hasattr(self.tts_service.tts, "invalidate_voices_cache"):
                self.tts_service.tts.invalidate_voices_cache("piper")
            self.voices_updated.emit()

    @Slot(str)
    def _test_voice(self, voice_id: str):
        self._on_synthesis_params_changed()
        sample_text = self.i18n.get("chat.status.voice_test_sample")
        if hasattr(self.tts_service, "speak"):
            self.tts_service.speak(sample_text, voice_id=voice_id)
