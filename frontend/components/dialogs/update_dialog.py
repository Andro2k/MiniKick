# frontend/components/dialogs/update_dialog.py

from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QProgressBar, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from frontend.components.dialogs.base_dialogs import ModernBaseDialog
from frontend.theme import COLOR_ACCENT
from frontend.utils import get_icon_colored

class UpdateDialog(ModernBaseDialog):
    download_requested = Signal() 
    restart_requested = Signal()

    def __init__(self, i18n, parent=None):
        self.i18n = i18n
        super().__init__(width=400, parent=parent)
        self.version = ""
        self.set_dialog_state("accent", QColor(83, 252, 24, 60))

        self.icon_check = QLabel()
        self.icon_check.setPixmap(get_icon_colored("circle-check.svg", COLOR_ACCENT, 48).pixmap(48, 48))
        self.icon_check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_check.hide()
        self.content_layout.addWidget(self.icon_check)

        self.lbl_top = QLabel(self.i18n.get("main.dialogs.update.top_searching"))
        self.lbl_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_top.setProperty("role", "text_accent")
        self.content_layout.addWidget(self.lbl_top)
        
        self.content_layout.addSpacing(5)

        self.lbl_title = QLabel(self.i18n.get("main.dialogs.update.title_default"))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setProperty("role", "h1")
        self.content_layout.addWidget(self.lbl_title)

        self.content_layout.addSpacing(10)

        self.lbl_subtitle = QLabel(self.i18n.get("main.dialogs.update.subtitle_connecting"))
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setWordWrap(True)
        self.lbl_subtitle.setProperty("role", "body")
        self.content_layout.addWidget(self.lbl_subtitle)

        self.content_layout.addSpacing(20)

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
        self.btn_primary.clicked.connect(lambda: None) 
        
        self.btn_secondary = QPushButton(self.i18n.get("main.dialogs.update.btn_close"))
        self.btn_secondary.setProperty("role", "action_outlined")
        self.btn_secondary.clicked.connect(self.reject)

        self.add_action_buttons(self.btn_primary, self.btn_secondary)

    def show_update_available(self, version: str):
        self.version = version
        self.icon_check.hide()
        self.lbl_top.setText(self.i18n.get("main.dialogs.update.top_available").replace("{version}", version))
        self.lbl_title.setText(self.i18n.get("main.dialogs.update.title_default"))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_restart_req"))
        self.progress_container.hide()
        
        self.btn_primary.setText(self.i18n.get("main.dialogs.update.btn_download"))
        self.btn_primary.setEnabled(True)
        try:
            self.btn_primary.clicked.disconnect()
        except RuntimeError:
            pass
            
        self.btn_primary.clicked.connect(self.download_requested.emit)
        self.btn_secondary.show()
    
    def show_downloading(self):
        self.icon_check.hide()
        self.lbl_top.setText(self.i18n.get("main.dialogs.update.top_available").replace("{version}", self.version))
        self.lbl_title.setText(self.i18n.get("main.dialogs.update.title_default"))
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
        self.set_dialog_state("neutral", QColor(0, 0, 0, 0))
        
        self.lbl_top.hide()
        self.icon_check.show()
        self.lbl_title.setText(self.i18n.get("main.dialogs.update.title_completed"))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_installed").replace("{version}", self.version))
        
        self.progress_bar.setValue(100)
        self.lbl_prog_val.setText("100%")
        
        self.btn_primary.setText(self.i18n.get("main.dialogs.update.btn_restart"))
        self.btn_primary.setEnabled(True)

        try:
            self.btn_primary.clicked.disconnect()
        except RuntimeError:
            pass
            
        self.btn_primary.clicked.connect(self.restart_requested.emit)
        self.btn_secondary.show()

    def show_no_update(self):
        self.set_dialog_state("neutral", QColor(0, 0, 0, 0))
        self.icon_check.hide()
        self.lbl_top.hide()
        self.lbl_title.setText(self.i18n.get("main.dialogs.update.title_up_to_date"))
        self.lbl_subtitle.setText(self.i18n.get("main.dialogs.update.subtitle_up_to_date"))
        self.progress_container.hide()
        
        self.btn_primary.hide()
        self.btn_secondary.setText(self.i18n.get("main.dialogs.update.btn_close"))
        self.btn_secondary.show()

    def show_error(self, message: str):
        self.set_dialog_state("danger", QColor(239, 68, 68, 60))
        
        self.lbl_top.setProperty("role", "text_danger")
        self.lbl_top.style().unpolish(self.lbl_top)
        self.lbl_top.style().polish(self.lbl_top)
        
        self.icon_check.hide()
        self.lbl_top.setText(self.i18n.get("main.dialogs.update.top_error"))
        self.lbl_title.setText(self.i18n.get("main.dialogs.update.title_error"))
        self.lbl_subtitle.setText(message)
        self.progress_container.hide()
        
        self.btn_primary.hide()
        self.btn_secondary.show()