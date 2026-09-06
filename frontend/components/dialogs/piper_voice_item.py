# frontend\components\dialogs\piper_voice_item.py

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, QSize, Signal
from frontend.common import (
    get_icon_colored, COLOR_NEUTRAL_400,
    MARGIN_MD, SPACING_SM, SPACING_MD, SPACING_2XS
)

class PiperVoiceItemWidget(QFrame):
    download_requested = Signal(str)
    delete_requested = Signal(str)
    test_requested = Signal(str)

    def __init__(self, voice_meta: dict, is_installed: bool, i18n, is_default: bool = False, parent=None):
        super().__init__(parent)
        self.voice_meta = voice_meta
        self.voice_id = voice_meta["id"]
        self.is_installed = is_installed
        self.i18n = i18n
        self.is_default = is_default or voice_meta.get("is_default", False)
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*MARGIN_MD)
        main_layout.setSpacing(SPACING_SM)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING_MD)

        lang_str = self.voice_meta.get("lang", "es_ES")
        badge_lbl = QLabel(lang_str.upper(), self)
        badge_lbl.setProperty("role", "code")
        badge_lbl.setFixedWidth(54)
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(SPACING_2XS)

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
        self.btn_test.setIcon(get_icon_colored("volume.svg", COLOR_NEUTRAL_400, size=14))
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
            self.btn_action.setEnabled(not self.is_default)
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
