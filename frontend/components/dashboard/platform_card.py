# frontend\components\dashboard\platform_card.py

from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from frontend.common import get_pixmap_colored, MARGIN_MD, SPACING_XS, SPACING_SM
from frontend.widgets import ModernButton, create_col_layout, create_row_layout

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
        layout = create_col_layout(spacing=SPACING_SM, margins=MARGIN_MD, parent=self)
        top_row = create_row_layout(spacing=SPACING_XS)

        self.lbl_icon = QLabel(self)
        self.lbl_icon.setPixmap(get_pixmap_colored(icon_file, self.brand_color, 20))
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_brand = QLabel(brand_name, self)
        self.lbl_brand.setProperty("role", "h3")

        self.lbl_status_pill = QLabel(self.i18n.get("dashboard.platforms.status_offline"), self)
        self.lbl_status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status_pill.setProperty("role", "status_pill")
        self._apply_pill_style("offline")

        top_row.addWidget(self.lbl_icon)
        top_row.addWidget(self.lbl_brand)
        top_row.addStretch(1)
        top_row.addWidget(self.lbl_status_pill)
        layout.addLayout(top_row)
        mid_row = create_row_layout(spacing=SPACING_XS)

        self.lbl_channel = QLabel(self.i18n.get("dashboard.platforms.disconnected"), self)
        self.lbl_channel.setProperty("role", "body")
        self.lbl_channel.setProperty("state", "normal")
        self.lbl_channel.setWordWrap(False)

        self.lbl_status = self.lbl_channel

        initial_msg_text = self.i18n.get("dashboard.platforms.messages_session").replace("{count}", "0")
        self.lbl_msgs = QLabel(initial_msg_text, self)
        self.lbl_msgs.setProperty("role", "caption")
        self.lbl_msgs.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        mid_row.addWidget(self.lbl_channel, 1)
        mid_row.addWidget(self.lbl_msgs, 0)
        layout.addLayout(mid_row)

        btn_key = self._BTN_CONNECT_KEYS.get(self.platform_id, "dashboard.connection.btn_connect_kick")
        self.btn_action = ModernButton(self.i18n.get(btn_key), role=self.button_role, parent=self)
        self.btn_action.setFixedHeight(28)
        layout.addWidget(self.btn_action)

    def _apply_pill_style(self, state: str):
        if state == "online":
            self.lbl_status_pill.setText(f"● {self.i18n.get('dashboard.platforms.status_online')}")
            self.lbl_status_pill.setProperty("state", "online")
        elif state == "connecting":
            self.lbl_status_pill.setText(f"◌ {self.i18n.get('dashboard.platforms.status_connecting')}")
            self.lbl_status_pill.setProperty("state", "connecting")
        else:
            self.lbl_status_pill.setText(f"○ {self.i18n.get('dashboard.platforms.status_offline')}")
            self.lbl_status_pill.setProperty("state", "offline")
        self.lbl_status_pill.style().unpolish(self.lbl_status_pill)
        self.lbl_status_pill.style().polish(self.lbl_status_pill)

    def update_state(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        tpl = self.i18n.get("dashboard.platforms.messages_session")
        self.lbl_msgs.setText(tpl.replace("{count}", str(msg_count)))

        if connecting:
            self._apply_pill_style("connecting")
            self.lbl_channel.setText(self.i18n.get("dashboard.platforms.connecting"))
            self.lbl_channel.setProperty("state", "info")
            self.btn_action.setEnabled(False)
            btn_key = self._BTN_CONNECTING_KEYS.get(self.platform_id, "dashboard.connection.btn_connecting_kick")
            self.btn_action.setText(self.i18n.get(btn_key))
        elif connected and channel:
            self._apply_pill_style("online")
            prefix = self.i18n.get("dashboard.platforms.channel_prefix")
            self.lbl_channel.setText(f"{prefix} <b>@{channel}</b>")
            self.lbl_channel.setProperty("state", "white")
            self.btn_action.setEnabled(False)
            btn_key = self._BTN_ACTIVE_KEYS.get(self.platform_id, "dashboard.connection.btn_active_kick")
            self.btn_action.setText(self.i18n.get(btn_key))
        else:
            self._apply_pill_style("offline")
            self.lbl_channel.setText(self.i18n.get("dashboard.platforms.disconnected"))
            self.lbl_channel.setProperty("state", "normal")
            self.btn_action.setEnabled(True)
            btn_key = self._BTN_CONNECT_KEYS.get(self.platform_id, "dashboard.connection.btn_connect_kick")
            self.btn_action.setText(self.i18n.get(btn_key))

        self.lbl_channel.style().unpolish(self.lbl_channel)
        self.lbl_channel.style().polish(self.lbl_channel)
