# frontend\components\dialogs\piper_voice_item.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, QSize, Signal
from frontend.common import (
    get_icon_colored, COLOR_NEUTRAL_400, COLOR_WHITE, COLOR_RED,
    SPACING_MD, SPACING_2XS, MARGIN_SETTING_ROW_COMPACT
)

class PiperVoiceItemWidget(QWidget):
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
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*MARGIN_SETTING_ROW_COMPACT)
        main_layout.setSpacing(SPACING_2XS)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING_MD)

        category = self.voice_meta.get("category", "natural")
        lang = self.voice_meta.get("lang", "es")
        
        badge_text = self._get_badge_text(category, lang)
        self.badge_lbl = QLabel(badge_text, self)
        self.badge_lbl.setProperty("role", "tag_badge" if category == "stream" else "badge")
        self.badge_lbl.setMinimumWidth(56)
        self.badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        header_layout.addWidget(self.badge_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addLayout(info_layout, stretch=1)

        self.lbl_status = QLabel(self)
        self.lbl_status.setProperty("role", "caption")
        self.update_status(self.is_installed)
        header_layout.addWidget(self.lbl_status, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.btn_test = QPushButton(self)
        self.btn_test.setIcon(get_icon_colored("volume-up-filled.svg", COLOR_WHITE, size=14))
        self.btn_test.setIconSize(QSize(14, 14))
        self.btn_test.setFixedSize(30, 30)
        self.btn_test.setProperty("role", "action_outlined")
        self.btn_test.setToolTip(self.i18n.get("chat.status.test_btn_tooltip"))
        self.btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test.clicked.connect(lambda: self.test_requested.emit(self.voice_id))
        self.btn_test.setVisible(self.is_installed)
        header_layout.addWidget(self.btn_test)

        self.btn_delete = QPushButton(self)
        self.btn_delete.setIcon(get_icon_colored("trash-filled.svg", COLOR_RED, size=13))
        self.btn_delete.setIconSize(QSize(13, 13))
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setProperty("role", "action_danger_outlined")
        self.btn_delete.setToolTip(self.i18n.get("piper_dialog.btn_delete_tooltip"))
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.voice_id))
        self.btn_delete.setVisible(self.is_installed and not self.is_default)
        header_layout.addWidget(self.btn_delete)

        self.btn_download = QPushButton(self)
        self.btn_download.setFixedHeight(30)
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.setText(self.i18n.get("piper_dialog.btn_download"))
        self.btn_download.setIcon(get_icon_colored("cloud-download-filled.svg", COLOR_WHITE, size=13))
        self.btn_download.setProperty("role", "action_outlined")
        self.btn_download.clicked.connect(lambda: self.download_requested.emit(self.voice_id))
        self.btn_download.setVisible(not self.is_installed and self._can_download())
        header_layout.addWidget(self.btn_download)

        main_layout.addLayout(header_layout)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _can_download(self) -> bool:
        if self.voice_meta.get("is_custom", False):
            return False
        return bool(self.voice_meta.get("onnx_url") or self.voice_meta.get("archive_url"))

    def _get_badge_text(self, category: str, lang: str) -> str:
        if category == "stream":
            return "STREAM"
        if lang == "es_MX":
            return "MX"
        if lang == "es_ES":
            return "ES"
        if lang == "es_AR":
            return "AR"
        if quality := self.voice_meta.get("quality"):
            if quality == "custom":
                return self.i18n.get("piper_dialog.badge_custom")
        return lang.upper()

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
        if hasattr(self, "btn_delete"):
            self.btn_delete.setVisible(is_installed and not self.is_default)
        if hasattr(self, "btn_download"):
            self.btn_download.setVisible(not is_installed and self._can_download())
            self.btn_download.setEnabled(True)
            self.btn_download.setText(self.i18n.get("piper_dialog.btn_download"))
            self.btn_download.setIcon(get_icon_colored("cloud-download-filled.svg", COLOR_WHITE, size=13))

    def set_downloading(self, downloading: bool, percent: int = 0):
        self.progress_bar.setVisible(downloading)
        self.progress_bar.setValue(percent)
        self.btn_download.setEnabled(not downloading)
        if downloading:
            self.btn_download.setText(f"{percent}%")
            self.btn_download.setIcon(get_icon_colored("cloud-download-filled.svg", COLOR_NEUTRAL_400, size=13))
            self.lbl_status.setText(self.i18n.get("piper_dialog.status_downloading"))
            self.lbl_status.setProperty("state", "info")
            self.lbl_status.style().unpolish(self.lbl_status)
            self.lbl_status.style().polish(self.lbl_status)
        else:
            self.btn_download.setText(self.i18n.get("piper_dialog.btn_download"))
            self.btn_download.setIcon(get_icon_colored("cloud-download-filled.svg", COLOR_WHITE, size=13))
