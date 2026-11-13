# frontend\dialogs\update_dialog.py

from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QProgressBar, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .base_dialog import ModernModal
from frontend.widgets import create_text_label
from frontend.common import get_pixmap_colored, get_assets_path, get_qcolor_with_alpha, Palette, BrandColors, Size

class UpdateDialog(ModernModal):
    download_requested = Signal()
    restart_requested = Signal()

    def __init__(self, i18n, parent=None):
        self.i18n = i18n
        super().__init__(
            title=self.i18n.get("dialogs.update.title_default"), icon_path=get_assets_path("icons/cloud-download-filled.svg"),
            icon_bg_color=BrandColors.GREEN, width=400, parent=parent
        )
        self.version = ""
        self.set_dialog_state("accent", get_qcolor_with_alpha(BrandColors.GREEN, 60))
        self.header_icon = self.header.findChild(QLabel, "dialog_icon_badge_glyph")

        self.lbl_subtitle = create_text_label(
            self.i18n.get("dialogs.update.subtitle_connecting"),
            role="text_body",
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.content_layout.addWidget(self.lbl_subtitle)

        self.content_layout.addSpacing(Size.SPACING_XL)

        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(*Size.Margin.MRG_NON)
        progress_layout.setSpacing(Size.SPACING_MD)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setProperty("role", "update_progress")
        progress_layout.addWidget(self.progress_bar)

        labels_layout = QHBoxLayout()
        self.lbl_prog_text = QLabel(self.i18n.get("dialogs.update.lbl_progress"))
        self.lbl_prog_text.setProperty("role", "text_body")
        self.lbl_prog_val = QLabel("0%")
        self.lbl_prog_val.setProperty("role", "text_body")

        labels_layout.addWidget(self.lbl_prog_text)
        labels_layout.addStretch()
        labels_layout.addWidget(self.lbl_prog_val)
        progress_layout.addLayout(labels_layout)

        self.content_layout.addWidget(self.progress_container)
        self.progress_container.hide()

        self.content_layout.addStretch()

        self.btn_primary = QPushButton(self.i18n.get("dialogs.update.btn_restart"))
        self.btn_primary.setProperty("role", "action_outlined")
        self.btn_primary.hide()

        self.btn_secondary = QPushButton(self.i18n.get("dialogs.update.btn_close"))
        self.btn_secondary.setProperty("role", "action_outlined")
        self.btn_secondary.clicked.connect(self.reject)

        self.add_action_buttons(self.btn_secondary, self.btn_primary, stretch_center=False)
        self._primary_connection = None

    def _refresh_presentation(self) -> None:
        self.footer_layout.invalidate()
        self.footer_layout.activate()
        self.content_layout.invalidate()
        self.content_layout.activate()
        self.body.setMinimumHeight(0)
        self.body.setMinimumHeight(self.body.sizeHint().height())
        self.container.layout().activate()
        self.container.adjustSize()
        self.adjustSize()
        self.container.repaint()
        self.footer.repaint()
        self.btn_secondary.repaint()
        self.btn_primary.repaint()

    def _set_header_icon(self, icon_name: str, color: str = Palette.NEUTRAL_050) -> None:
        if self.header_icon:
            self.header_icon.setPixmap(
                get_pixmap_colored(
                    icon_name,
                    color_str=color,
                    size=self.header_icon.width(),
                    dpr=self.devicePixelRatioF(),
                )
            )

    def show_update_available(self, version: str):
        self.version = version
        self._set_header_icon("cloud-download-filled.svg")

        self.title_lbl.setText(self.i18n.get("dialogs.update.top_available").replace("{version}", version))
        self.lbl_subtitle.setText(self.i18n.get("dialogs.update.subtitle_available"))
        self.progress_container.hide()

        self.btn_primary.setText(self.i18n.get("dialogs.update.btn_download"))
        self.btn_primary.show()
        self.btn_primary.setEnabled(True)

        if self._primary_connection:
            self.btn_primary.clicked.disconnect(self._primary_connection)

        self._primary_connection = self.btn_primary.clicked.connect(self.download_requested.emit)

        self.btn_secondary.show()
        self._refresh_presentation()

    def show_downloading(self):
        self.title_lbl.setText(self.i18n.get("dialogs.update.title_default"))
        self.lbl_subtitle.setText(self.i18n.get("dialogs.update.subtitle_downloading"))

        self.progress_bar.setValue(0)
        self.lbl_prog_val.setText("0%")
        self.progress_container.show()

        self.btn_primary.setText(self.i18n.get("dialogs.update.btn_downloading"))
        self.btn_primary.setEnabled(False)
        self.btn_primary.show()
        self.btn_secondary.hide()
        self._refresh_presentation()

    def update_progress(self, percentage: int):
        self.progress_bar.setValue(percentage)
        self.lbl_prog_val.setText(f"{percentage}%")

    def show_complete(self):
        self.set_dialog_state("accent", get_qcolor_with_alpha(BrandColors.GREEN, 60))
        self._set_header_icon("cloud-check-filled.svg")

        self.title_lbl.setText(self.i18n.get("dialogs.update.title_completed"))
        self.lbl_subtitle.setText(self.i18n.get("dialogs.update.subtitle_restart_req"))

        self.progress_bar.setValue(100)
        self.lbl_prog_val.setText("100%")

        self.btn_primary.setText(self.i18n.get("dialogs.update.btn_restart"))
        self.btn_primary.setEnabled(True)
        self.btn_primary.show()

        if self._primary_connection:
            self.btn_primary.clicked.disconnect(self._primary_connection)

        self._primary_connection = self.btn_primary.clicked.connect(self.restart_requested.emit)

        self.btn_secondary.show()
        self._refresh_presentation()

    def show_no_update(self):
        self.set_dialog_state("neutral", QColor(Qt.GlobalColor.transparent))
        self._set_header_icon("cloud-check-filled.svg")

        self.title_lbl.setText(self.i18n.get("dialogs.update.title_up_to_date"))
        self.lbl_subtitle.setText(self.i18n.get("dialogs.update.subtitle_up_to_date"))
        self.progress_container.hide()

        self.btn_primary.hide()
        self.btn_secondary.setText(self.i18n.get("dialogs.update.btn_close"))
        self.btn_secondary.show()
        self._refresh_presentation()

    def show_error(self, message: str):
        self.set_dialog_state("danger", get_qcolor_with_alpha(BrandColors.RED, 60))
        self._set_header_icon("alert-triangle-filled.svg", BrandColors.RED)

        self.title_lbl.setText(self.i18n.get("dialogs.update.title_error"))
        self.lbl_subtitle.setText(message)
        self.progress_container.hide()

        self.btn_primary.hide()
        self.btn_secondary.show()
        self._refresh_presentation()
