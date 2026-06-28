# frontend\dialogs\update_dialog.py

from frontend.common.theme import COLOR_BG_BASE
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QProgressBar, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from frontend.dialogs.base_dialog import ModernModal
from frontend.common.theme import COLOR_ACCENT, COLOR_DANGER, COLOR_INFO
from frontend.common.utils import get_icon_colored, get_assets_path

class UpdateDialog(ModernModal):
    download_requested = Signal() 
    restart_requested = Signal()

    def __init__(self, i18n, parent=None):
        self.i18n = i18n
        super().__init__(
            title=self.i18n.get("main.dialogs.update.title_default"), 
            icon_path=get_assets_path("icons/cloud-download.svg"), 
            icon_bg_color=COLOR_INFO,
            width=400, 
            parent=parent
        )
        self.version = ""
        self.set_dialog_state("accent", QColor(59, 130, 246, 60))

        self.header_icon = None
        for lbl in self.container.findChildren(QLabel):
            if lbl.pixmap():
                self.header_icon = lbl
                break

        self.lbl_subtitle = QLabel(self.i18n.get("main.dialogs.update.subtitle_connecting"))
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setWordWrap(True)
        self.lbl_subtitle.setProperty("role", "body")
        self.content_layout.addWidget(self.lbl_subtitle)

        self.content_layout.addSpacing(15)

        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setProperty("role", "update_progress")
        progress_layout.addWidget(self.progress_bar)

        labels_layout = QHBoxLayout()
        self.lbl_prog_text = QLabel(self.i18n.get("main.dialogs.update.lbl_progress"))
        self.lbl_prog_text.setProperty("role", "body")
        self.lbl_prog_val = QLabel("0%")
        self.lbl_prog_val.setProperty("role", "body")
        
        labels_layout.addWidget(self.lbl_prog_text)
        labels_layout.addStretch()
        labels_layout.addWidget(self.lbl_prog_val)
        progress_layout.addLayout(labels_layout)
        
        self.content_layout.addWidget(self.progress_container)
        self.progress_container.hide() 

        self.content_layout.addStretch()

        self.btn_primary = QPushButton(self.i18n.get("main.dialogs.update.btn_restart"))
        self.btn_primary.setProperty("role", "action_accent")
        
        self.btn_secondary = QPushButton(self.i18n.get("main.dialogs.update.btn_close"))
        self.btn_secondary.setProperty("role", "action_outlined")
        self.btn_secondary.clicked.connect(self.reject)

        self.add_action_buttons(self.btn_secondary, self.btn_primary, stretch_center=False)
        self._primary_connection = None

    def show_update_available(self, version: str):
        self.version = version
        if self.header_icon:
            self.header_icon.setPixmap(get_icon_colored("cloud-download.svg", COLOR_BG_BASE, 48).pixmap(48, 48))
            
        self.title_lbl.setText(self.i18n.get("main.dialogs.update.top_available").replace("{version}", version))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_restart_req"))
        self.progress_container.hide()
        
        self.btn_primary.setText(self.i18n.get("main.dialogs.update.btn_download"))
        self.btn_primary.show()
        self.btn_primary.setEnabled(True)
        
        if self._primary_connection:
            self.btn_primary.clicked.disconnect(self._primary_connection)
            
        self._primary_connection = self.btn_primary.clicked.connect(self.download_requested.emit)
        
        self.btn_secondary.show()
    
    def show_downloading(self):
        self.title_lbl.setText(self.i18n.get("main.dialogs.update.title_default"))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_downloading"))
        
        self.progress_bar.setValue(0)
        self.lbl_prog_val.setText("0%")
        self.progress_container.show()
        
        self.btn_primary.setText(self.i18n.get("main.dialogs.update.btn_downloading"))
        self.btn_primary.setEnabled(False)
        self.btn_secondary.hide() 

    def update_progress(self, percentage: int):
        self.progress_bar.setValue(percentage)
        self.lbl_prog_val.setText(f"{percentage}%")

    def show_complete(self):
        self.set_dialog_state("accent", QColor(83, 252, 24, 60))
        if self.header_icon:
            self.header_icon.setPixmap(get_icon_colored("cloud-check.svg", COLOR_ACCENT, 48).pixmap(48, 48))
            
        self.title_lbl.setText(self.i18n.get("main.dialogs.update.title_completed"))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_installed").replace("{version}", self.version))
        
        self.progress_bar.setValue(100)
        self.lbl_prog_val.setText("100%")
        
        self.btn_primary.setText(self.i18n.get("main.dialogs.update.btn_restart"))
        self.btn_primary.setEnabled(True)
        self.btn_primary.show()

        if self._primary_connection:
            self.btn_primary.clicked.disconnect(self._primary_connection)
            
        self._primary_connection = self.btn_primary.clicked.connect(self.restart_requested.emit)
        
        self.btn_secondary.show()

    def show_no_update(self):
        self.set_dialog_state("neutral", QColor(0, 0, 0, 0))
        if self.header_icon:
            self.header_icon.setPixmap(get_icon_colored("cloud-check.svg", COLOR_BG_BASE, 48).pixmap(48, 48))
            
        self.title_lbl.setText(self.i18n.get("main.dialogs.update.title_up_to_date"))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_up_to_date"))
        self.progress_container.hide()
        
        self.btn_primary.hide()
        self.btn_secondary.setText(self.i18n.get("main.dialogs.update.btn_close"))
        self.btn_secondary.show()

    def show_error(self, message: str):
        self.set_dialog_state("danger", QColor(239, 68, 68, 60))
        if self.header_icon:
            self.header_icon.setPixmap(get_icon_colored("alert-triangle.svg", COLOR_DANGER, 48).pixmap(48, 48))
            
        self.title_lbl.setText(self.i18n.get("main.dialogs.update.title_error"))
        self.lbl_subtitle.setText(message)
        self.progress_container.hide()
        
        self.btn_primary.hide()
        self.btn_secondary.show()