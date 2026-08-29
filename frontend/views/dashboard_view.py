# frontend\views\dashboard_view.py

from PySide6.QtWidgets import (
    QBoxLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPainterPath
from frontend.common.theme import (
    COLOR_BLACK, COLOR_WHITE, COLOR_RED, COLOR_NEUTRAL_800, COLOR_NEUTRAL_700,
    COLOR_NEUTRAL_500, COLOR_NEUTRAL_400, COLOR_GREEN, COLOR_BLUE, COLOR_PURPLE,
    COLOR_TIKTOK, COLOR_TWITCH, COLOR_YOUTUBE
)
from frontend.common import create_circular_pixmap, get_icon_colored, get_pixmap_colored
from frontend.widgets import (
    BaseView, StatCard, SettingRow, ModernCard,
    ModernButton, ModernSwitch, ModernDivider
)

class SegmentedDistributionBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self._segments = []
        self._cached_clip_path = None
        self._cached_rect = None

    def set_data(self, data: list[tuple[float, str]]):
        self._segments = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        if self._cached_rect != rect:
            self._cached_rect = rect
            self._cached_clip_path = QPainterPath()
            self._cached_clip_path.addRoundedRect(QRectF(rect), 8, 8)
            
        painter.setClipPath(self._cached_clip_path)
        
        total_p = sum(p for p, _ in self._segments)
        if total_p <= 0:
            painter.fillRect(rect, QColor(COLOR_NEUTRAL_800))
            return
            
        current_x = 0.0
        w = float(self.width())
        h = float(self.height())
        for p, color in self._segments:
            seg_width = (p / total_p) * w
            painter.fillRect(QRectF(current_x, 0, seg_width, h), QColor(color))
            current_x += seg_width


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

        self.lbl_msgs = QLabel("0 msgs", self)
        self.lbl_msgs.setProperty("role", "caption")
        self.lbl_msgs.setStyleSheet(f"color: {COLOR_NEUTRAL_400}; font-weight: 500;")

        header_layout.addWidget(self.lbl_icon)
        header_layout.addWidget(self.lbl_brand)
        header_layout.addStretch(1)
        header_layout.addWidget(self.lbl_msgs)
        layout.addLayout(header_layout)

        self.lbl_status = QLabel(self.i18n.get("dashboard.platforms.disconnected"), self)
        self.lbl_status.setProperty("role", "body")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet(f"color: {COLOR_NEUTRAL_400};")
        layout.addWidget(self.lbl_status)

        btn_key = self._BTN_CONNECT_KEYS.get(self.platform_id, "dashboard.connection.btn_connect_kick")
        self.btn_action = ModernButton(self.i18n.get(btn_key), role=self.button_role)
        self.btn_action.setFixedHeight(30)
        layout.addWidget(self.btn_action)

    def update_state(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        tpl = self.i18n.get("dashboard.platforms.messages_session")
        self.lbl_msgs.setText(tpl.replace("{count}", str(msg_count)))

        if connecting:
            self.lbl_status.setText(self.i18n.get("dashboard.platforms.connecting"))
            self.lbl_status.setStyleSheet(f"color: {COLOR_BLUE};")
            self.btn_action.setEnabled(False)
            btn_key = self._BTN_CONNECTING_KEYS.get(self.platform_id, "dashboard.connection.btn_connecting_kick")
            self.btn_action.setText(self.i18n.get(btn_key))
        elif connected and channel:
            prefix = self.i18n.get("dashboard.platforms.channel_prefix")
            self.lbl_status.setText(f"{prefix} <b>@{channel}</b>")
            self.lbl_status.setStyleSheet(f"color: {COLOR_WHITE};")
            self.btn_action.setEnabled(False)
            btn_key = self._BTN_ACTIVE_KEYS.get(self.platform_id, "dashboard.connection.btn_active_kick")
            self.btn_action.setText(self.i18n.get(btn_key))
        else:
            self.lbl_status.setText(self.i18n.get("dashboard.platforms.disconnected"))
            self.lbl_status.setStyleSheet(f"color: {COLOR_NEUTRAL_400};")
            self.btn_action.setEnabled(True)
            btn_key = self._BTN_CONNECT_KEYS.get(self.platform_id, "dashboard.connection.btn_connect_kick")
            self.btn_action.setText(self.i18n.get(btn_key))


class DashboardView(BaseView):
    connect_requested = Signal()
    twitch_connect_requested = Signal()
    youtube_connect_requested = Signal()
    tiktok_connect_requested = Signal()
    autostart_toggled = Signal(bool)
    reauth_requested = Signal()
    reauth_kick_requested = Signal()
    reauth_twitch_requested = Signal()
    channel_tab_changed = Signal(str)
    
    _STATS_CARDS_ATTR = "_stats_cols"
    _SESSION_CARDS_ATTR = "_session_cols"
    _PLATFORM_CARDS_ATTR = "_platform_cols"
    
    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="dashboard.header.title", subtitle_key="dashboard.header.subtitle", parent=parent)
        self._stats_cols = -1
        self._session_cols = -1
        self._platform_cols = -1
        self._last_top_row_dir = None
        self._current_profile_platform = "kick"
        self._setup_ui()

    def _setup_ui(self):
        self.banner_scopes_kick = QFrame()
        self.banner_scopes_kick.setProperty("role", "banner_danger")
        self.banner_layout_kick = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.banner_scopes_kick)
        self.banner_scopes_kick.setVisible(False)
        self.lbl_warn_text_kick = QLabel()
        self.lbl_warn_text_kick.setWordWrap(True)
        self.btn_reauth_kick = ModernButton(self.i18n.get("dashboard.banner.btn_update_kick"), role="action_danger_border")
        self.btn_reauth_kick.clicked.connect(self._on_reauth_kick_clicked)
        lbl_kick_icon = QLabel()
        lbl_kick_icon.setPixmap(get_pixmap_colored("brand-kick.svg", COLOR_GREEN, 24))
        self.banner_layout_kick.addWidget(lbl_kick_icon)
        self.banner_layout_kick.addWidget(self.lbl_warn_text_kick, stretch=1)
        self.banner_layout_kick.addWidget(self.btn_reauth_kick)
        self.main_layout.addWidget(self.banner_scopes_kick)

        self.banner_scopes_twitch = QFrame()
        self.banner_scopes_twitch.setProperty("role", "banner_danger")
        self.banner_layout_twitch = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.banner_scopes_twitch)
        self.banner_scopes_twitch.setVisible(False)
        self.lbl_warn_text_twitch = QLabel()
        self.lbl_warn_text_twitch.setWordWrap(True)
        self.btn_reauth_twitch = ModernButton(self.i18n.get("dashboard.banner.btn_update_twitch"), role="action_danger_border")
        self.btn_reauth_twitch.clicked.connect(self._on_reauth_twitch_clicked)
        lbl_twitch_icon = QLabel()
        lbl_twitch_icon.setPixmap(get_pixmap_colored("brand-twitch.svg", COLOR_TWITCH, 24))
        self.banner_layout_twitch.addWidget(lbl_twitch_icon)
        self.banner_layout_twitch.addWidget(self.lbl_warn_text_twitch, stretch=1)
        self.banner_layout_twitch.addWidget(self.btn_reauth_twitch)
        self.main_layout.addWidget(self.banner_scopes_twitch)

        self.banner_scopes = self.banner_scopes_kick
        self.lbl_warn_text = self.lbl_warn_text_kick
        self.btn_reauth = self.btn_reauth_kick
        self.banner_layout = self.banner_layout_kick
        
        self._setup_platforms_hub()
        
        self._setup_channel_profile_section()

        self._setup_global_analytics_section()
        self.main_layout.addStretch()

    def _setup_platforms_hub(self):
        hub_card = ModernCard(parent=self, margin=12, spacing=10)

        self.sw_autostart = ModernSwitch()
        self.sw_autostart.toggled.connect(self.autostart_toggled.emit)
        
        row_autostart = SettingRow(
            "plug.svg", 
            self.i18n.get("dashboard.connection.autostart_title"), 
            self.i18n.get("dashboard.connection.autostart_desc"), 
            self.sw_autostart
        )
        hub_card.addWidget(row_autostart)
        hub_card.addWidget(ModernDivider())

        platforms_container = QWidget(self)
        self.platforms_grid = QGridLayout(platforms_container)
        self.platforms_grid.setContentsMargins(0, 0, 0, 0)
        self.platforms_grid.setSpacing(10)

        self.card_kick = PlatformStatusCard(
            self.i18n, "kick", self.i18n.get("dashboard.platforms.kick_title"),
            "brand-kick.svg", COLOR_GREEN, "action_kick", parent=self
        )
        self.card_kick.btn_action.clicked.connect(self.connect_requested.emit)
        self.btn_connect = self.card_kick.btn_action

        self.card_twitch = PlatformStatusCard(
            self.i18n, "twitch", self.i18n.get("dashboard.platforms.twitch_title"),
            "brand-twitch.svg", COLOR_TWITCH, "action_twitch", parent=self
        )
        self.card_twitch.btn_action.clicked.connect(self.twitch_connect_requested.emit)
        self.btn_connect_twitch = self.card_twitch.btn_action

        self.card_youtube = PlatformStatusCard(
            self.i18n, "youtube", self.i18n.get("dashboard.platforms.youtube_title"),
            "brand-youtube.svg", COLOR_YOUTUBE, "action_youtube", parent=self
        )
        self.card_youtube.btn_action.clicked.connect(self.youtube_connect_requested.emit)
        self.btn_connect_youtube = self.card_youtube.btn_action

        self.card_tiktok = PlatformStatusCard(
            self.i18n, "tiktok", self.i18n.get("dashboard.platforms.tiktok_title"),
            "brand-tiktok.svg", COLOR_TIKTOK, "action_tiktok", parent=self
        )
        self.card_tiktok.btn_action.clicked.connect(self.tiktok_connect_requested.emit)
        self.btn_connect_tiktok = self.card_tiktok.btn_action

        self.platform_cards = [self.card_kick, self.card_twitch, self.card_youtube, self.card_tiktok]
        for i, card in enumerate(self.platform_cards):
            self.platforms_grid.addWidget(card, 0, i)

        hub_card.addWidget(platforms_container)

        self.status_label = QLabel(self.i18n.get("dashboard.connection.status_waiting"))
        self.status_label.setVisible(False)
        hub_card.addWidget(self.status_label)

        self.main_layout.addWidget(hub_card)

    def _setup_channel_profile_section(self):
        self.profile_wrapper = QWidget(self)
        self.profile_wrapper_layout = QVBoxLayout(self.profile_wrapper)
        self.profile_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self.profile_wrapper_layout.setSpacing(10)

        self.tabs_container = QWidget(self)
        self.tabs_layout = QHBoxLayout(self.tabs_container)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(8)

        self.btn_tab_kick = ModernButton(self.i18n.get("dashboard.profile.tab_kick"), role="action_kick")
        self.btn_tab_kick.setFixedHeight(30)
        self.btn_tab_kick.setIcon(get_icon_colored("brand-kick.svg", COLOR_BLACK, 14))
        self.btn_tab_kick.clicked.connect(lambda: self.channel_tab_changed.emit("kick"))

        self.btn_tab_twitch = ModernButton(self.i18n.get("dashboard.profile.tab_twitch"), role="action_twitch")
        self.btn_tab_twitch.setFixedHeight(30)
        self.btn_tab_twitch.setIcon(get_icon_colored("brand-twitch.svg", COLOR_WHITE, 14))
        self.btn_tab_twitch.clicked.connect(lambda: self.channel_tab_changed.emit("twitch"))

        self.tabs_layout.addWidget(self.btn_tab_kick)
        self.tabs_layout.addWidget(self.btn_tab_twitch)
        self.tabs_layout.addStretch(1)
        self.tabs_container.setVisible(False)
        self.profile_wrapper_layout.addWidget(self.tabs_container)

        self.profile_container = QWidget(self)
        profile_layout = QVBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(10)

        self.top_row_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.top_row_layout.setSpacing(12) 

        avatar_card = ModernCard(parent=self)
        avatar_card.card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(110, 110)
        self.lbl_avatar.setScaledContents(True) 
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setText("?")
        avatar_card.addWidget(self.lbl_avatar)

        info_card = ModernCard(parent=self)
        info_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.lbl_username = QLabel("-")
        self.lbl_username.setProperty("role", "h1")
        self.lbl_username.setWordWrap(True)

        self.lbl_bio = QLabel("-")
        self.lbl_bio.setProperty("role", "body")
        self.lbl_bio.setWordWrap(True)

        info_card.addWidget(self.lbl_username)
        info_card.addWidget(self.lbl_bio)
        
        self.top_row_layout.addWidget(avatar_card)
        self.top_row_layout.addWidget(info_card, stretch=1)
        profile_layout.addLayout(self.top_row_layout)

        stats_container = QWidget(self)
        self.stats_grid = QGridLayout(stats_container)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        self.stats_grid.setSpacing(10)
        
        self.card_followers = StatCard(self.i18n.get("dashboard.stats.followers"), "users.svg")
        self.card_room = StatCard(self.i18n.get("dashboard.stats.room_id"), "hash.svg")
        self.card_category = StatCard(self.i18n.get("dashboard.stats.category"), "category.svg") 
        self.card_affiliate = StatCard(self.i18n.get("dashboard.stats.affiliate"), "star.svg")
        self.card_created = StatCard(self.i18n.get("dashboard.stats.created_at"), "calendar.svg")
        self.card_next_schedule = StatCard(self.i18n.get("dashboard.stats.next_schedule"), "clock.svg")

        self.creator_stats_cards = [
            self.card_followers, self.card_room, self.card_category,
            self.card_affiliate, self.card_created, self.card_next_schedule
        ]
        for i, card in enumerate(self.creator_stats_cards):
            self.stats_grid.addWidget(card, i // 3, i % 3)

        profile_layout.addWidget(stats_container)
        self.profile_container.setVisible(False)
        self.profile_wrapper_layout.addWidget(self.profile_container)

        self.disconnected_container = ModernCard(parent=self, margin=20, spacing=8)
        self.disconnected_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        empty_header = QHBoxLayout()
        empty_header.setSpacing(12)

        lbl_empty_icon = QLabel(self)
        lbl_empty_icon.setPixmap(get_pixmap_colored("users.svg", COLOR_NEUTRAL_500, 32))
        lbl_empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_text_layout = QVBoxLayout()
        empty_text_layout.setSpacing(4)

        self.lbl_empty_title = QLabel(self.i18n.get("dashboard.profile.no_channel_title"), self)
        self.lbl_empty_title.setProperty("role", "h3")

        self.lbl_empty_desc = QLabel(self.i18n.get("dashboard.profile.no_channel_desc"), self)
        self.lbl_empty_desc.setProperty("role", "body")
        self.lbl_empty_desc.setStyleSheet(f"color: {COLOR_NEUTRAL_400};")
        self.lbl_empty_desc.setWordWrap(True)

        empty_text_layout.addWidget(self.lbl_empty_title)
        empty_text_layout.addWidget(self.lbl_empty_desc)

        empty_header.addWidget(lbl_empty_icon)
        empty_header.addLayout(empty_text_layout, stretch=1)
        self.disconnected_container.addLayout(empty_header)

        self.lbl_disconnected_title = self.lbl_empty_title
        self.lbl_disconnected_desc = self.lbl_empty_desc

        self.profile_wrapper_layout.addWidget(self.disconnected_container)
        self.main_layout.addWidget(self.profile_wrapper)

    def _setup_global_analytics_section(self):
        analytics_container = QWidget(self)
        analytics_layout = QVBoxLayout(analytics_container)
        analytics_layout.setContentsMargins(0, 0, 0, 0)
        analytics_layout.setSpacing(14)

        analytics_layout.addWidget(ModernDivider())

        lbl_activity_title = QLabel(self.i18n.get("dashboard.analytics.title"))
        lbl_activity_title.setProperty("role", "h2")
        analytics_layout.addWidget(lbl_activity_title)

        bar_card = ModernCard(parent=self, margin=10, spacing=6)
        lbl_dist_title = QLabel(self.i18n.get("dashboard.analytics.distribution_title"))
        lbl_dist_title.setProperty("role", "caption")
        lbl_dist_title.setStyleSheet(f"color: {COLOR_NEUTRAL_400}; font-weight: 600;")
        bar_card.addWidget(lbl_dist_title)

        self.session_bar = SegmentedDistributionBar()
        bar_card.addWidget(self.session_bar)
        analytics_layout.addWidget(bar_card)

        session_stats_container = QWidget(self)
        self.session_grid = QGridLayout(session_stats_container)
        self.session_grid.setContentsMargins(0, 0, 0, 0)
        self.session_grid.setSpacing(10)

        self.card_msg_processed = StatCard(self.i18n.get("dashboard.session.messages"), "message.svg", "0")
        self.card_cmd_executed = StatCard(self.i18n.get("dashboard.session.commands"), "code.svg", "0")
        self.card_timers_sent = StatCard(self.i18n.get("dashboard.session.timers"), "clock.svg", "0")
        self.card_spam_blocked = StatCard(self.i18n.get("dashboard.session.spam"), "shield-half.svg", "0")

        self.session_cards = [
            self.card_msg_processed, self.card_cmd_executed,
            self.card_timers_sent, self.card_spam_blocked
        ]
        for i, card in enumerate(self.session_cards):
            self.session_grid.addWidget(card, 0, i)

        analytics_layout.addWidget(session_stats_container)

        self.bottom_analytics_layout = QHBoxLayout()
        self.bottom_analytics_layout.setSpacing(12)

        self.top_commands_card = ModernCard(parent=self, margin=12, spacing=8)
        self.top_commands_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_top_cmds = QLabel(self.i18n.get("dashboard.analytics.top_commands_title"))
        lbl_top_cmds.setProperty("role", "h3")
        self.top_commands_card.addWidget(lbl_top_cmds)

        self.top_commands_container = QVBoxLayout()
        self.top_commands_container.setSpacing(6)
        self.lbl_no_commands = QLabel(self.i18n.get("dashboard.analytics.no_commands_used"))
        self.lbl_no_commands.setProperty("role", "body")
        self.lbl_no_commands.setStyleSheet(f"color: {COLOR_NEUTRAL_500};")
        self.top_commands_container.addWidget(self.lbl_no_commands)
        self.top_commands_card.addLayout(self.top_commands_container)

        self.modules_card = ModernCard(parent=self, margin=12, spacing=8)
        self.modules_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_modules_title = QLabel(self.i18n.get("dashboard.analytics.modules_summary_title"))
        lbl_modules_title.setProperty("role", "h3")
        self.modules_card.addWidget(lbl_modules_title)

        self.modules_grid = QGridLayout()
        self.modules_grid.setSpacing(8)

        self.lbl_active_cmds_val = QLabel("0")
        self.lbl_active_cmds_val.setProperty("role", "h2")
        lbl_active_cmds_text = QLabel(self.i18n.get("dashboard.analytics.active_commands"))
        lbl_active_cmds_text.setProperty("role", "caption")

        self.lbl_active_timers_val = QLabel("0")
        self.lbl_active_timers_val.setProperty("role", "h2")
        lbl_active_timers_text = QLabel(self.i18n.get("dashboard.analytics.active_timers"))
        lbl_active_timers_text.setProperty("role", "caption")

        self.lbl_active_rewards_val = QLabel("0")
        self.lbl_active_rewards_val.setProperty("role", "h2")
        lbl_active_rewards_text = QLabel(self.i18n.get("dashboard.analytics.active_rewards"))
        lbl_active_rewards_text.setProperty("role", "caption")

        self.modules_grid.addWidget(self.lbl_active_cmds_val, 0, 0)
        self.modules_grid.addWidget(lbl_active_cmds_text, 1, 0)
        self.modules_grid.addWidget(self.lbl_active_timers_val, 0, 1)
        self.modules_grid.addWidget(lbl_active_timers_text, 1, 1)
        self.modules_grid.addWidget(self.lbl_active_rewards_val, 0, 2)
        self.modules_grid.addWidget(lbl_active_rewards_text, 1, 2)

        self.modules_card.addLayout(self.modules_grid)

        self.bottom_analytics_layout.addWidget(self.top_commands_card, stretch=3)
        self.bottom_analytics_layout.addWidget(self.modules_card, stretch=2)

        analytics_layout.addLayout(self.bottom_analytics_layout)
        self.main_layout.addWidget(analytics_container)

    def set_kick_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_kick.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def set_twitch_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_twitch.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def set_youtube_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_youtube.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def set_tiktok_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_tiktok.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def update_platform_messages(self, kick: int = 0, twitch: int = 0, youtube: int = 0, tiktok: int = 0):
        segments = []
        if kick > 0:
            segments.append((kick, COLOR_GREEN))
        if twitch > 0:
            segments.append((twitch, COLOR_TWITCH))
        if youtube > 0:
            segments.append((youtube, COLOR_RED))
        if tiktok > 0:
            segments.append((tiktok, COLOR_TIKTOK))
        self.session_bar.set_data(segments)

    def render_channel_profile(self, platform: str, profile_data: dict | None, connected_platforms: list[str], avatar_bytes: bytes | None = None):
        self._current_profile_platform = platform

        if len(connected_platforms) > 1:
            self.tabs_container.setVisible(True)
            self.btn_tab_kick.setVisible("kick" in connected_platforms)
            self.btn_tab_twitch.setVisible("twitch" in connected_platforms)
            self.btn_tab_kick.setEnabled(platform != "kick")
            self.btn_tab_twitch.setEnabled(platform != "twitch")
        else:
            self.tabs_container.setVisible(False)

        if not profile_data:
            self.profile_container.setVisible(False)
            self.disconnected_container.setVisible(True)
            return

        self.disconnected_container.setVisible(False)
        self.profile_container.setVisible(True)

        username = profile_data.get("display_name") or profile_data.get("username", "-")
        if profile_data.get("is_verified", False):
            username += " ✓"
        bio = profile_data.get("bio", "-") or "-"
        self.lbl_username.setText(username)
        self.lbl_bio.setText(bio)

        followers_str = f"{profile_data.get('followers', 0):,}"
        room_str = str(profile_data.get("room_id") or profile_data.get("broadcaster_id") or "-")
        category = profile_data.get("last_category") or profile_data.get("category") or "-"

        if platform == "twitch":
            self.card_room.lbl_title.setText(self.i18n.get("dashboard.stats.broadcaster_id"))
            self.card_affiliate.lbl_title.setText(self.i18n.get("dashboard.stats.account_type"))
            broadcaster_type = profile_data.get("broadcaster_type", "")
            affiliate_text = broadcaster_type.capitalize() if broadcaster_type else self.i18n.get("dashboard.platforms.connected")
        else:
            self.card_room.lbl_title.setText(self.i18n.get("dashboard.stats.room_id"))
            self.card_affiliate.lbl_title.setText(self.i18n.get("dashboard.stats.affiliate"))
            is_affiliate = profile_data.get("is_affiliate", False)
            affiliate_text = self.i18n.get("main.controllers.dashboard.affiliate") if is_affiliate else self.i18n.get("main.controllers.dashboard.not_affiliate")

        created_str = profile_data.get("created_at", "-") or "-"

        self.card_followers.set_value(followers_str)
        self.card_room.set_value(room_str)
        self.card_category.set_value(category)
        self.card_affiliate.set_value(affiliate_text)
        self.card_created.set_value(created_str)

        if avatar_bytes:
            self.set_avatar_from_bytes(avatar_bytes)
        else:
            self.lbl_avatar.setPixmap(QPixmap())
            self.lbl_avatar.setText("?")

    def update_analytics_summary(self, analytics: dict):
        if not analytics:
            return

        top_commands = analytics.get("top_commands", [])
        while self.top_commands_container.count() > 0:
            item = self.top_commands_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count() > 0:
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        if not top_commands:
            lbl_none = QLabel(self.i18n.get("dashboard.analytics.no_commands_used"))
            lbl_none.setProperty("role", "body")
            lbl_none.setStyleSheet(f"color: {COLOR_NEUTRAL_500};")
            self.top_commands_container.addWidget(lbl_none)
        else:
            max_cnt = max((cmd.get("count", 1) for cmd in top_commands), default=1)
            usages_str = self.i18n.get("dashboard.analytics.usages")
            for idx, cmd in enumerate(top_commands):
                row = QHBoxLayout()
                row.setSpacing(8)
                
                lbl_rank = QLabel(f"#{idx + 1}")
                lbl_rank.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: bold; min-width: 20px;")
                
                lbl_trigger = QLabel(cmd.get("trigger", ""))
                lbl_trigger.setProperty("role", "body")
                lbl_trigger.setStyleSheet("font-weight: 600; min-width: 90px;")
                
                pbar = QProgressBar()
                pbar.setFixedHeight(8)
                pbar.setTextVisible(False)
                pbar.setRange(0, max_cnt)
                pbar.setValue(cmd.get("count", 0))
                pbar.setStyleSheet(f"QProgressBar {{ background-color: {COLOR_NEUTRAL_700}; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {COLOR_BLUE}; border-radius: 4px; }}")
                
                lbl_cnt = QLabel(f"{cmd.get('count', 0)} {usages_str}")
                lbl_cnt.setProperty("role", "caption")
                lbl_cnt.setStyleSheet(f"color: {COLOR_NEUTRAL_400}; min-width: 55px;")
                
                row.addWidget(lbl_rank)
                row.addWidget(lbl_trigger)
                row.addWidget(pbar, stretch=1)
                row.addWidget(lbl_cnt)
                self.top_commands_container.addLayout(row)

        self.lbl_active_cmds_val.setText(str(analytics.get("active_commands", 0)))
        self.lbl_active_timers_val.setText(str(analytics.get("active_timers", 0)))
        self.lbl_active_rewards_val.setText(str(analytics.get("total_rewards", 0)))

    def update_next_schedule(self, schedule_text: str):
        if hasattr(self, "card_next_schedule"):
            self.card_next_schedule.set_value(schedule_text or "-")

    def set_autostart_state(self, enabled: bool):
        self.sw_autostart.blockSignals(True)
        self.sw_autostart.setChecked(enabled)
        self.sw_autostart.blockSignals(False)

    @staticmethod
    def _fmt_metric(count: int, total: int) -> str:
        pct = (count / total * 100) if total > 0 else 0.0
        return f"{count}   ·   {pct:.1f}%"

    def _relayout_grid(self, grid, cards: list, cols: int, attr: str):
        if cols != getattr(self, attr, -1):
            setattr(self, attr, cols)
            for i, card in enumerate(cards):
                grid.addWidget(card, i // cols, i % cols)

    def update_connection_status(self, is_connecting: bool, has_error: bool = False, error_msg: str = ""):
        if is_connecting:
            self.set_kick_status(connecting=True)
        elif has_error:
            self.set_kick_status(connected=False)

    def update_profile_info(self, username: str, bio: str):
        self.lbl_username.setText(username)
        self.lbl_bio.setText(bio)

    def update_stats(self, followers: str, room_id: str, category: str, affiliate_text: str, vods_text: str, created_at: str = "-", next_schedule: str = "-"):
        self.card_followers.set_value(followers)
        self.card_room.set_value(room_id)
        self.card_category.set_value(category)
        self.card_affiliate.set_value(affiliate_text)
        self.card_vods.set_value(vods_text)
        self.card_next_schedule.set_value(next_schedule)

    def update_session_metrics(self, msg_count: int, cmd_count: int, timer_count: int, spam_count: int):
        total = msg_count + cmd_count + timer_count + spam_count
        metrics = [
            (self.card_msg_processed, msg_count, COLOR_PURPLE),
            (self.card_cmd_executed, cmd_count, COLOR_BLUE),
            (self.card_timers_sent, timer_count, COLOR_GREEN),
            (self.card_spam_blocked, spam_count, COLOR_RED),
        ]
        for card, count, _ in metrics:
            card.set_value(self._fmt_metric(count, total))

    def set_avatar_from_bytes(self, image_data: bytes):
        pixmap = create_circular_pixmap(image_data)
        if not pixmap.isNull():
            self.lbl_avatar.setPixmap(pixmap)
            self.lbl_avatar.setProperty("has_image", True)
            self.lbl_avatar.style().unpolish(self.lbl_avatar)
            self.lbl_avatar.style().polish(self.lbl_avatar)
    
    def reset_to_disconnected(self):
        self.set_kick_status(connected=False)
        self.lbl_avatar.setPixmap(QPixmap())

    def _on_reauth_kick_clicked(self):
        self.reauth_kick_requested.emit()

    def _on_reauth_twitch_clicked(self):
        self.reauth_twitch_requested.emit()

    def show_scope_warning(self, missing_scopes: dict | list):
        if not missing_scopes:
            self.banner_scopes_kick.setVisible(False)
            self.banner_scopes_twitch.setVisible(False)
            return

        if isinstance(missing_scopes, dict):
            kick_keys = missing_scopes.get("kick", [])
            twitch_keys = missing_scopes.get("twitch", [])
        elif isinstance(missing_scopes, list):
            kick_keys = [k for k in missing_scopes if "kick" in k or "twitch" not in k]
            twitch_keys = [k for k in missing_scopes if "twitch" in k]
        else:
            kick_keys, twitch_keys = [], []

        if kick_keys:
            scope_names = ", ".join(f"<b>{self.i18n.get(key)}</b>" for key in kick_keys)
            prefix = self.i18n.get("dashboard.banner.text_prefix_kick")
            self.lbl_warn_text_kick.setText(f"{prefix} {scope_names}.")
            self.banner_scopes_kick.setVisible(True)
        else:
            self.banner_scopes_kick.setVisible(False)

        if twitch_keys:
            scope_names = ", ".join(f"<b>{self.i18n.get(key)}</b>" for key in twitch_keys)
            prefix = self.i18n.get("dashboard.banner.text_prefix_twitch")
            self.lbl_warn_text_twitch.setText(f"{prefix} {scope_names}.")
            self.banner_scopes_twitch.setVisible(True)
        else:
            self.banner_scopes_twitch.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        
        banner_dir = QBoxLayout.Direction.TopToBottom if width < 480 else QBoxLayout.Direction.LeftToRight
        align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop if width < 480 else Qt.AlignmentFlag.AlignVCenter
        
        if hasattr(self, 'banner_layout_kick'):
            self.banner_layout_kick.setDirection(banner_dir)
            self.lbl_warn_text_kick.setAlignment(align)

        if hasattr(self, 'banner_layout_twitch'):
            self.banner_layout_twitch.setDirection(banner_dir)
            self.lbl_warn_text_twitch.setAlignment(align)

        if hasattr(self, 'platforms_grid') and hasattr(self, 'platform_cards'):
            plat_cols = 1 if width < 550 else (2 if width < 900 else 4)
            self._relayout_grid(self.platforms_grid, self.platform_cards, plat_cols, self._PLATFORM_CARDS_ATTR)
        
        if hasattr(self, 'stats_grid') and hasattr(self, 'creator_stats_cards'):
            stats_cols = 1 if width < 650 else (2 if width < 950 else 3)
            self._relayout_grid(self.stats_grid, self.creator_stats_cards, stats_cols, self._STATS_CARDS_ATTR)
        
        if hasattr(self, 'session_grid') and hasattr(self, 'session_cards'):
            session_cols = 1 if width < 650 else (2 if width < 950 else 4)
            self._relayout_grid(self.session_grid, self.session_cards, session_cols, self._SESSION_CARDS_ATTR)

        if hasattr(self, 'top_row_layout'):
            top_row_dir = QBoxLayout.Direction.TopToBottom if width < 600 else QBoxLayout.Direction.LeftToRight
            if self._last_top_row_dir != top_row_dir:
                self._last_top_row_dir = top_row_dir
                self.top_row_layout.setDirection(top_row_dir)

        if hasattr(self, 'bottom_analytics_layout'):
            bottom_dir = QBoxLayout.Direction.TopToBottom if width < 750 else QBoxLayout.Direction.LeftToRight
            self.bottom_analytics_layout.setDirection(bottom_dir)
