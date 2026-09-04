# frontend\components\alerts\overlay_card.py

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QBoxLayout
from PySide6.QtCore import Signal
from frontend.widgets import ModernCard, ModernButton
from frontend.common import get_pixmap_colored, COLOR_GREEN

class AlertsOverlayCard(ModernCard):
    copy_url_requested = Signal()
    open_browser_requested = Signal()

    def __init__(self, alerts_overlay_url: str, i18n, parent=None):
        super().__init__(parent=parent, margin=12, spacing=8)
        self.alerts_overlay_url = alerts_overlay_url
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        card_header = QHBoxLayout()
        card_header.setSpacing(8)

        icon_link = QLabel(parent=self)
        icon_link.setPixmap(get_pixmap_colored("link.svg", COLOR_GREEN, size=20))

        lbl_obs_title = QLabel(self.i18n.get("alerts.overlay_card.title"), parent=self)
        lbl_obs_title.setProperty("role", "h3")

        card_header.addWidget(icon_link)
        card_header.addWidget(lbl_obs_title)
        card_header.addStretch()
        self.addLayout(card_header)

        lbl_obs_desc = QLabel(self.i18n.get("alerts.overlay_card.desc"), parent=self)
        lbl_obs_desc.setProperty("role", "body")
        lbl_obs_desc.setWordWrap(True)
        self.addWidget(lbl_obs_desc)

        self.url_box = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.url_box.setContentsMargins(0, 0, 0, 0)
        self.url_box.setSpacing(8)

        self.edit_overlay_url = QLineEdit(self.alerts_overlay_url, parent=self)
        self.edit_overlay_url.setReadOnly(True)
        self.edit_overlay_url.setMinimumWidth(0)

        self.url_actions_layout = QHBoxLayout()
        self.url_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.url_actions_layout.setSpacing(8)

        self.btn_copy_url = ModernButton(
            text=self.i18n.get("alerts.overlay_card.copy_btn"),
            role="action_accent",
            icon_name="clipboard-text.svg",
            icon_size=15,
            parent=self
        )
        self.btn_copy_url.clicked.connect(self.copy_url_requested.emit)

        self.btn_open_browser = ModernButton(
            text=self.i18n.get("alerts.overlay_card.open_btn"),
            role="action_outlined",
            icon_name="eye.svg",
            icon_size=15,
            parent=self
        )
        self.btn_open_browser.clicked.connect(self.open_browser_requested.emit)

        self.url_actions_layout.addWidget(self.btn_copy_url)
        self.url_actions_layout.addWidget(self.btn_open_browser)
        self.url_actions_layout.addStretch()

        self.url_box.addWidget(self.edit_overlay_url, stretch=1)
        self.url_box.addLayout(self.url_actions_layout)
        self.addLayout(self.url_box)

    def set_overlay_url(self, url: str):
        self.alerts_overlay_url = url
        self.edit_overlay_url.setText(url)

    def set_responsive_direction(self, direction: QBoxLayout.Direction):
        if self.url_box.direction() != direction:
            self.url_box.setDirection(direction)
