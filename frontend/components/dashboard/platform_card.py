# frontend\components\dashboard\platform_card.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from frontend.common import get_pixmap_colored
from frontend.widgets import ModernButton

class PlatformStatusCard(QFrame):
    _BTN_CONNECT_KEYS = {
        "kick": "dashboard.connection.btn_connect_kick",
        "twitch": "dashboard.connection.btn_connect_twitch",
        "youtube": "dashboard.connection.btn_connect_youtube",
        "tiktok": "dashboard.connection.btn_connect_tiktok",
    }
    _BTN_ACTIVE_KEYS = {
        "kick": "dashboard.connection.btn_active_kick",
        "twitch": "dashboard.connection.btn_active_twitch",
        "youtube": "dashboard.connection.btn_active_youtube",
        "tiktok": "dashboard.connection.btn_active_tiktok",
    }
    _BTN_CONNECTING_KEYS = {
        "kick": "dashboard.connection.btn_connecting_kick",
        "twitch": "dashboard.connection.btn_connecting_twitch",
        "youtube": "dashboard.connection.btn_connecting_youtube",
        "tiktok": "dashboard.connection.btn_connecting_tiktok",
    }

    def __init__(self, i18n, platform_id: str, brand_name: str, icon_file: str, brand_color: str, button_role: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.platform_id = platform_id
        self.brand_color = brand_color
        self.button_role = button_role
        self.setProperty("role", "card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._setup_ui(brand_name, icon_file)

    def _setup_ui(self, brand_name: str, icon_file: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.lbl_icon = QLabel(self)
        self.lbl_icon.setPixmap(get_pixmap_colored(icon_file, self.brand_color, 20))
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_brand = QLabel(brand_name, self)
        self.lbl_brand.setProperty("role", "h3")

        initial_msg_text = self.i18n.get("dashboard.platforms.messages_session").replace("{count}", "0")
        self.lbl_msgs = QLabel(initial_msg_text, self)
        self.lbl_msgs.setProperty("role", "caption")

        header_layout.addWidget(self.lbl_icon)
        header_layout.addWidget(self.lbl_brand)
        header_layout.addStretch(1)
        header_layout.addWidget(self.lbl_msgs)
        layout.addLayout(header_layout)

        self.lbl_status = QLabel(self.i18n.get("dashboard.platforms.disconnected"), self)
        self.lbl_status.setProperty("role", "body")
        self.lbl_status.setProperty("state", "normal")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        btn_key = self._BTN_CONNECT_KEYS.get(self.platform_id, "dashboard.connection.btn_connect_kick")
        self.btn_action = ModernButton(self.i18n.get(btn_key), role=self.button_role)
        layout.addWidget(self.btn_action)

    def update_state(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        tpl = self.i18n.get("dashboard.platforms.messages_session")
        self.lbl_msgs.setText(tpl.replace("{count}", str(msg_count)))

        if connecting:
            self.lbl_status.setText(self.i18n.get("dashboard.platforms.connecting"))
            self.lbl_status.setProperty("state", "info")
            self.btn_action.setEnabled(False)
            btn_key = self._BTN_CONNECTING_KEYS.get(self.platform_id, "dashboard.connection.btn_connecting_kick")
            self.btn_action.setText(self.i18n.get(btn_key))
        elif connected and channel:
            prefix = self.i18n.get("dashboard.platforms.channel_prefix")
            self.lbl_status.setText(f"{prefix} <b>@{channel}</b>")
            self.lbl_status.setProperty("state", "white")
            self.btn_action.setEnabled(False)
            btn_key = self._BTN_ACTIVE_KEYS.get(self.platform_id, "dashboard.connection.btn_active_kick")
            self.btn_action.setText(self.i18n.get(btn_key))
        else:
            self.lbl_status.setText(self.i18n.get("dashboard.platforms.disconnected"))
            self.lbl_status.setProperty("state", "normal")
            self.btn_action.setEnabled(True)
            btn_key = self._BTN_CONNECT_KEYS.get(self.platform_id, "dashboard.connection.btn_connect_kick")
            self.btn_action.setText(self.i18n.get(btn_key))

        self.lbl_status.style().unpolish(self.lbl_status)
        self.lbl_status.style().polish(self.lbl_status)
