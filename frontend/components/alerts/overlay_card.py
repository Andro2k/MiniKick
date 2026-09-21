# frontend\components\alerts\overlay_card.py

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QBoxLayout, QSizePolicy
from PySide6.QtCore import Signal, QSize, Qt
from frontend.widgets import ModernCard, ModernButton
from frontend.common import (
    get_pixmap_colored, COLOR_NEUTRAL_400,
    MARGIN_NONE, MARGIN_MD, SPACING_2XS, SPACING_SM, SPACING_MD
)

class AlertsOverlayCard(ModernCard):
    copy_url_requested = Signal()
    open_browser_requested = Signal()

    def __init__(self, alerts_overlay_url: str, i18n, parent=None):
        super().__init__(parent=parent, margin=MARGIN_MD, spacing=SPACING_SM)
        self.alerts_overlay_url = alerts_overlay_url
        self.i18n = i18n
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._setup_ui()

    def _setup_ui(self):
        main_row = QHBoxLayout()
        main_row.setContentsMargins(*MARGIN_NONE)
        main_row.setSpacing(SPACING_MD)

        icon_link = QLabel(parent=self)
        icon_link.setPixmap(get_pixmap_colored("link-filled.svg", COLOR_NEUTRAL_400, size=18))

        text_col = QVBoxLayout()
        text_col.setContentsMargins(*MARGIN_NONE)
        text_col.setSpacing(SPACING_2XS)

        lbl_obs_title = QLabel(self.i18n.get("alerts.overlay_card.title"), parent=self)
        lbl_obs_title.setProperty("role", "h3")

        lbl_obs_desc = QLabel(self.i18n.get("alerts.overlay_card.desc"), parent=self)
        lbl_obs_desc.setProperty("role", "body")
        lbl_obs_desc.setWordWrap(True)

        text_col.addWidget(lbl_obs_title)
        text_col.addWidget(lbl_obs_desc)

        self.btn_copy_url = ModernButton(
            text=self.i18n.get("common.buttons.copy"),
            role="action_outlined",
            icon_name="copy-filled.svg",
            icon_size=15,
            parent=self
        )
        self.btn_copy_url.clicked.connect(self.copy_url_requested.emit)

        main_row.addWidget(icon_link, alignment=Qt.AlignmentFlag.AlignTop)
        main_row.addLayout(text_col, stretch=1)
        main_row.addWidget(self.btn_copy_url, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.addLayout(main_row)

        self.edit_overlay_url = QLineEdit(self.alerts_overlay_url, parent=self)
        self.edit_overlay_url.hide()

        self.btn_open_browser = ModernButton(
            text=self.i18n.get("alerts.overlay_card.open_btn"),
            role="action_outlined",
            icon_name="eye-filled.svg",
            icon_size=15,
            parent=self
        )
        self.btn_open_browser.hide()

        self.url_box = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.url_actions_layout = QHBoxLayout()

    def set_overlay_url(self, url: str):
        self.alerts_overlay_url = url
        self.edit_overlay_url.setText(url)

    def set_responsive_direction(self, direction: QBoxLayout.Direction):
        pass

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self.minimumSizeHint().height())
