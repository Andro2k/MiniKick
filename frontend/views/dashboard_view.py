# frontend\views\dashboard_view.py

import logging
from PySide6.QtWidgets import QBoxLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy, QProgressBar
from PySide6.QtCore import Qt, Signal, QUrl
from frontend.common import create_circular_pixmap, get_pixmap_colored, Palette, BrandColors, Size
from frontend.widgets import BaseView, StatCard, ModernCard, ModernButton
from frontend.components.dashboard import PlatformDistributionRing, PlatformStatusCard, DashboardChattersTable

logger = logging.getLogger("minikick.views.dashboard")


class DashboardView(BaseView):
    connect_requested = Signal()
    twitch_connect_requested = Signal()
    youtube_connect_requested = Signal()
    tiktok_connect_requested = Signal()
    reauth_requested = Signal()
    reauth_kick_requested = Signal()
    reauth_twitch_requested = Signal()
    channel_tab_changed = Signal(str)
    top_chatters_date_changed = Signal(str)
    activate_chatters_requested = Signal()
    _SESSION_CARDS_ATTR = "_session_cols"
    _PLATFORM_CARDS_ATTR = "_platform_cols"
    _CHANNEL_BADGES_ATTR = "_channel_badge_cols"

    def __init__(self, i18n, browser_service=None, parent=None):
        super().__init__(i18n=i18n, title_key="dashboard.header.title", subtitle_key="dashboard.header.subtitle", parent=parent)
        self.browser_service = browser_service
        self._session_cols = 4
        self._platform_cols = 4
        self._last_top_row_dir = None
        self._current_profile_platform = "kick"
        self._current_avatar_bytes = None
        self._channel_badge_cols = -1
        self._rendered_top_commands = None
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout.setSpacing(Size.SPACING_MD)

        self._setup_platforms_hub()
        self._setup_welcome_section()

        self.banner_scopes_kick = QFrame(self)
        self.banner_scopes_kick.setProperty("role", "banner_scope_card")
        self.banner_scopes_kick.setProperty("state", "kick")
        self.banner_layout_kick = QHBoxLayout(self.banner_scopes_kick)
        self.banner_layout_kick.setContentsMargins(*Size.Margin.MRG_LRG)
        self.banner_layout_kick.setSpacing(Size.SPACING_MD)
        self.banner_scopes_kick.setVisible(False)
        self.lbl_warn_text_kick = QLabel(self.banner_scopes_kick)
        self.lbl_warn_text_kick.setWordWrap(True)
        self.btn_reauth_kick = ModernButton(self.i18n.get("dashboard.banner.btn_update_kick"), role="action_kick", parent=self.banner_scopes_kick)
        self.btn_reauth_kick.clicked.connect(self._on_reauth_kick_clicked)
        lbl_kick_icon = QLabel(self.banner_scopes_kick)
        lbl_kick_icon.setPixmap(get_pixmap_colored("brand-kick.svg", BrandColors.GREEN, 24))
        lbl_kick_icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.banner_layout_kick.addWidget(lbl_kick_icon, 0, Qt.AlignmentFlag.AlignTop)
        self.banner_layout_kick.addWidget(self.lbl_warn_text_kick, 1)
        self.banner_layout_kick.addWidget(self.btn_reauth_kick, 0, Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addWidget(self.banner_scopes_kick)

        self.banner_scopes_twitch = QFrame(self)
        self.banner_scopes_twitch.setProperty("role", "banner_scope_card")
        self.banner_scopes_twitch.setProperty("state", "twitch")
        self.banner_layout_twitch = QHBoxLayout(self.banner_scopes_twitch)
        self.banner_layout_twitch.setContentsMargins(*Size.Margin.MRG_LRG)
        self.banner_layout_twitch.setSpacing(Size.SPACING_MD)
        self.banner_scopes_twitch.setVisible(False)
        self.lbl_warn_text_twitch = QLabel(self.banner_scopes_twitch)
        self.lbl_warn_text_twitch.setWordWrap(True)
        self.btn_reauth_twitch = ModernButton(self.i18n.get("dashboard.banner.btn_update_twitch"), role="action_twitch", parent=self.banner_scopes_twitch)
        self.btn_reauth_twitch.clicked.connect(self._on_reauth_twitch_clicked)
        lbl_twitch_icon = QLabel(self.banner_scopes_twitch)
        lbl_twitch_icon.setPixmap(get_pixmap_colored("brand-twitch.svg", BrandColors.TWITCH, 24))
        lbl_twitch_icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.banner_layout_twitch.addWidget(lbl_twitch_icon, 0, Qt.AlignmentFlag.AlignTop)
        self.banner_layout_twitch.addWidget(self.lbl_warn_text_twitch, 1)
        self.banner_layout_twitch.addWidget(self.btn_reauth_twitch, 0, Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addWidget(self.banner_scopes_twitch)

        self.banner_scopes = self.banner_scopes_kick
        self.lbl_warn_text = self.lbl_warn_text_kick
        self.btn_reauth = self.btn_reauth_kick
        self.banner_layout = self.banner_layout_kick

        self._setup_global_analytics_section()
        self.main_layout.addStretch()

    def _setup_welcome_section(self):
        self.welcome_card = QFrame(self)
        self.welcome_card.setProperty("role", "dashboard_welcome")
        welcome_layout = QVBoxLayout(self.welcome_card)
        welcome_layout.setContentsMargins(*Size.Margin.MRG_MED)
        welcome_layout.setSpacing(Size.SPACING_MD)

        self.lbl_welcome_title = QLabel(self.i18n.get("dashboard.welcome.title"), self.welcome_card)
        self.lbl_welcome_title.setProperty("role", "h2")
        welcome_layout.addWidget(self.lbl_welcome_title)

        self.lbl_welcome_subtitle = QLabel(self.i18n.get("dashboard.welcome.subtitle"), self.welcome_card)
        self.lbl_welcome_subtitle.setProperty("role", "body")
        self.lbl_welcome_subtitle.setWordWrap(True)
        welcome_layout.addWidget(self.lbl_welcome_subtitle)

        self.welcome_content_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.welcome_content_layout.setContentsMargins(*Size.Margin.MRG_NON)
        self.welcome_content_layout.setSpacing(Size.SPACING_SM)
        welcome_layout.addLayout(self.welcome_content_layout)

        self.distribution_panel = QFrame(self.welcome_card)
        self.distribution_panel.setProperty("role", "dashboard_distribution_panel")
        profile_layout = QVBoxLayout(self.distribution_panel)
        profile_layout.setContentsMargins(*Size.Margin.MRG_MED)
        profile_layout.setSpacing(Size.SPACING_XS)

        self.avatar_container = QWidget(self.distribution_panel)
        avatar_layout = QGridLayout(self.avatar_container)
        avatar_layout.setContentsMargins(*Size.Margin.MRG_NON)
        self.platform_distribution_ring = PlatformDistributionRing(self.avatar_container)
        avatar_layout.addWidget(self.platform_distribution_ring, 0, 0)
        self.btn_switch_channel = ModernButton(
            "",
            role="action_outlined",
            icon_name="repeat-filled.svg",
            parent=self.avatar_container,
        )
        self.btn_switch_channel.setFixedSize(30, 30)
        self.btn_switch_channel.setToolTip(self.i18n.get("dashboard.welcome.switch_account"))
        self.btn_switch_channel.clicked.connect(self._switch_channel_account)
        avatar_layout.addWidget(
            self.btn_switch_channel,
            0,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        self.btn_switch_channel.setVisible(False)
        profile_layout.addWidget(self.avatar_container, 0, Qt.AlignmentFlag.AlignHCenter)

        self.channel_identity_row = QHBoxLayout()
        self.channel_identity_row.setSpacing(Size.SPACING_SM)
        self.lbl_welcome_channel_name = QLabel(
            self.i18n.get("dashboard.welcome.unlinked_channel"), self.distribution_panel
        )
        self.lbl_welcome_channel_name.setProperty("role", "dashboard_channel_name")
        self.lbl_welcome_channel_name.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.lbl_welcome_channel_name.setWordWrap(True)
        self.channel_identity_row.addStretch(1)
        self.channel_identity_row.addWidget(self.lbl_welcome_channel_name)

        self.btn_open_channel = ModernButton(
            "",
            role="btn_ghost",
            icon_name="link-filled.svg",
            parent=self.distribution_panel,
        )
        self.btn_open_channel.setToolTip(self.i18n.get("dashboard.profile.open_channel"))
        self.btn_open_channel.clicked.connect(self._on_open_channel_clicked)
        self.btn_open_channel.setFixedSize(28, 28)
        self.btn_open_channel.setVisible(False)
        self.channel_identity_row.addWidget(self.btn_open_channel)
        self.channel_identity_row.addStretch(1)
        profile_layout.addLayout(self.channel_identity_row)

        self.lbl_welcome_channel_description = QLabel(
            self.i18n.get("dashboard.welcome.unlinked_description"), self.distribution_panel
        )
        self.lbl_welcome_channel_description.setProperty("role", "dashboard_channel_description")
        self.lbl_welcome_channel_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_welcome_channel_description.setWordWrap(True)
        profile_layout.addWidget(self.lbl_welcome_channel_description)

        self.channel_badges_container = QWidget(self)
        self.channel_badges_grid = QGridLayout(self.channel_badges_container)
        self.channel_badges_grid.setContentsMargins(*Size.Margin.MRG_NON)
        self.channel_badges_grid.setSpacing(Size.SPACING_MD)
        self.channel_badges = {}
        badge_specs = (
            ("followers", "dashboard.stats.followers", "users-filled.svg"),
            ("created", "dashboard.stats.created_at", "calendar-days-filled.svg"),
            ("category", "dashboard.stats.category", "globe-filled.svg"),
            ("identifier", "dashboard.stats.room_id", "hashtag-filled.svg"),
        )
        for badge_key, title_key, icon_name in badge_specs:
            badge = StatCard(self.i18n.get(title_key), icon_name, "-", self.channel_badges_container)
            self.channel_badges[badge_key] = {
                "title": badge.lbl_title,
                "value": badge,
            }
        self.channel_badge_cards = [badge["value"] for badge in self.channel_badges.values()]
        self._relayout_grid(
            self.channel_badges_grid,
            self.channel_badge_cards,
            self._channel_badge_cols,
            self._CHANNEL_BADGES_ATTR,
        )
        self.channel_badges_container.setVisible(False)

        self.welcome_content_layout.addWidget(self.distribution_panel, 1)
        self.welcome_content_layout.addWidget(self.platforms_container, 2)
        self.main_layout.addWidget(self.welcome_card)
        self.main_layout.addWidget(self.channel_badges_container)

    def _setup_platforms_hub(self):
        self.platforms_container = QWidget(self)
        self.platforms_grid = QGridLayout(self.platforms_container)
        self.platforms_grid.setContentsMargins(*Size.Margin.MRG_NON)
        self.platforms_grid.setSpacing(Size.SPACING_SM)

        self.card_kick = PlatformStatusCard(
            self.i18n, "kick", self.i18n.get("dashboard.platforms.kick_title"),
            "brand-kick.svg", "action_kick", parent=self
        )
        self.card_kick.btn_action.clicked.connect(self.connect_requested.emit)
        self.btn_connect = self.card_kick.btn_action

        self.card_twitch = PlatformStatusCard(
            self.i18n, "twitch", self.i18n.get("dashboard.platforms.twitch_title"),
            "brand-twitch.svg", "action_twitch", parent=self
        )
        self.card_twitch.btn_action.clicked.connect(self.twitch_connect_requested.emit)
        self.btn_connect_twitch = self.card_twitch.btn_action

        self.card_youtube = PlatformStatusCard(
            self.i18n, "youtube", self.i18n.get("dashboard.platforms.youtube_title"),
            "brand-youtube.svg", "action_youtube", parent=self
        )
        self.card_youtube.btn_action.clicked.connect(self.youtube_connect_requested.emit)
        self.btn_connect_youtube = self.card_youtube.btn_action

        self.card_tiktok = PlatformStatusCard(
            self.i18n, "tiktok", self.i18n.get("dashboard.platforms.tiktok_title"),
            "brand-tiktok.svg", "action_tiktok", parent=self
        )
        self.card_tiktok.btn_action.clicked.connect(self.tiktok_connect_requested.emit)
        self.btn_connect_tiktok = self.card_tiktok.btn_action

        self.platform_cards = [self.card_kick, self.card_twitch, self.card_youtube, self.card_tiktok]
        self._relayout_grid(self.platforms_grid, self.platform_cards, 2, self._PLATFORM_CARDS_ATTR)
        for card in self.platform_cards:
            card.update_message_share(0, 0)

        self.platforms_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _setup_global_analytics_section(self):
        analytics_container = QWidget(self)
        analytics_layout = QVBoxLayout(analytics_container)
        analytics_layout.setContentsMargins(*Size.Margin.MRG_NON)
        analytics_layout.setSpacing(Size.SPACING_MD)

        session_stats_container = QWidget(self)
        self.session_grid = QGridLayout(session_stats_container)
        self.session_grid.setContentsMargins(*Size.Margin.MRG_NON)
        self.session_grid.setSpacing(Size.SPACING_MD)

        self.card_msg_processed = StatCard(self.i18n.get("dashboard.session.messages"), "dialog-filled.svg", "0")
        self.card_cmd_executed = StatCard(self.i18n.get("dashboard.session.commands"), "chat-square-code-filled.svg", "0")
        self.card_timers_sent = StatCard(self.i18n.get("dashboard.session.timers"), "clock-filled.svg", "0")
        self.card_spam_blocked = StatCard(self.i18n.get("dashboard.session.spam"), "shield-filled.svg", "0")

        self.session_cards = [
            self.card_msg_processed, self.card_cmd_executed,
            self.card_timers_sent, self.card_spam_blocked
        ]
        for i, card in enumerate(self.session_cards):
            self.session_grid.addWidget(card, 0, i)

        analytics_layout.addWidget(session_stats_container)

        self.bottom_analytics_layout = QHBoxLayout()
        self.bottom_analytics_layout.setSpacing(Size.SPACING_MD)

        self.chatters_table = DashboardChattersTable(self.i18n, parent=self)
        self.chatters_table.date_selected.connect(self.top_chatters_date_changed.emit)
        self.chatters_table.activate_widget_requested.connect(self.activate_chatters_requested.emit)
        self.bottom_analytics_layout.addWidget(self.chatters_table, stretch=3)

        right_col_widget = QWidget(self)
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.setContentsMargins(*Size.Margin.MRG_NON)
        right_col_layout.setSpacing(Size.SPACING_MD)

        self.top_commands_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.top_commands_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_top_cmds = QLabel(self.i18n.get("dashboard.analytics.top_commands_title"))
        lbl_top_cmds.setProperty("role", "h3")
        self.top_commands_card.addWidget(lbl_top_cmds)

        self.top_commands_container = QVBoxLayout()
        self.top_commands_container.setSpacing(Size.SPACING_SM)
        self.lbl_no_commands = QLabel(self.i18n.get("dashboard.analytics.no_commands_used"))
        self.lbl_no_commands.setProperty("role", "body")
        self.top_commands_container.addWidget(self.lbl_no_commands)
        self.top_commands_card.addLayout(self.top_commands_container)
        right_col_layout.addWidget(self.top_commands_card)

        self.modules_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.modules_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_modules_title = QLabel(self.i18n.get("dashboard.analytics.modules_summary_title"))
        lbl_modules_title.setProperty("role", "h3")
        self.modules_card.addWidget(lbl_modules_title)

        self.modules_grid = QGridLayout()
        self.modules_grid.setSpacing(Size.SPACING_SM)

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
        right_col_layout.addWidget(self.modules_card)

        self.bottom_analytics_layout.addWidget(right_col_widget, stretch=2)

        analytics_layout.addLayout(self.bottom_analytics_layout)
        self.main_layout.addWidget(analytics_container)

    def render_top_chatters(self, chatters: list[dict], total_messages: int = 0):
        if hasattr(self, "chatters_table"):
            self.chatters_table.set_chatters(chatters, total_messages=total_messages)

    def populate_chatter_dates(self, dates: list[str]):
        if hasattr(self, "chatters_table"):
            self.chatters_table.populate_available_dates(dates)

    def set_chatters_widget_active(self, is_active: bool):
        if hasattr(self, "chatters_table"):
            self.chatters_table.set_widget_active(is_active)

    def set_kick_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_kick.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def set_twitch_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_twitch.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def set_youtube_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_youtube.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def set_tiktok_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        self.card_tiktok.update_state(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

    def update_platform_messages(self, kick: int = 0, twitch: int = 0, youtube: int = 0, tiktok: int = 0):
        message_counts = {
            "kick": max(0, int(kick)),
            "twitch": max(0, int(twitch)),
            "youtube": max(0, int(youtube)),
            "tiktok": max(0, int(tiktok)),
        }
        total_messages = sum(message_counts.values())
        segments = []
        platform_styles = (
            ("kick", BrandColors.GREEN, self.card_kick),
            ("twitch", BrandColors.TWITCH, self.card_twitch),
            ("youtube", BrandColors.RED, self.card_youtube),
            ("tiktok", BrandColors.TIKTOK, self.card_tiktok),
        )
        for platform_id, color, card in platform_styles:
            count = message_counts[platform_id]
            if count:
                segments.append((count, color))
            card.update_message_share(count, total_messages)
        self.platform_distribution_ring.set_data(segments)

    def render_channel_profile(self, platform: str, profile_data: dict | None, connected_platforms: list[str], avatar_bytes: bytes | None = None):
        self._current_profile_platform = platform
        self.btn_switch_channel.setVisible("kick" in connected_platforms and "twitch" in connected_platforms)

        if not profile_data:
            self._current_channel_username = ""
            self.lbl_welcome_channel_name.setText(self.i18n.get("dashboard.welcome.unlinked_channel"))
            self.lbl_welcome_channel_description.setText(self.i18n.get("dashboard.welcome.unlinked_description"))
            self.btn_open_channel.setEnabled(False)
            self.btn_open_channel.setVisible(False)
            self.channel_badges_container.setVisible(False)
            self._current_avatar_bytes = None
            self.platform_distribution_ring.set_avatar(None)
            self._clear_channel_badges()
            return

        raw_user = profile_data.get("username", "-")
        self._current_channel_username = raw_user
        username = profile_data.get("display_name") or raw_user
        if profile_data.get("is_verified", False):
            username += " \u2713"
        bio = profile_data.get("bio") or self.i18n.get("dashboard.welcome.channel_description_unavailable")
        self.lbl_welcome_channel_name.setText(username)
        self.lbl_welcome_channel_description.setText(bio)
        self.btn_open_channel.setEnabled(bool(raw_user and raw_user != "-"))
        self.btn_open_channel.setVisible(True)
        self.channel_badges_container.setVisible(True)

        followers = profile_data.get("followers", 0)
        followers_text = self.i18n.get("dashboard.profile.followers_count").replace(
            "{count}", f"{followers:,}"
        )
        identifier = profile_data.get("room_id") or profile_data.get("broadcaster_id") or "-"
        category = profile_data.get("last_category") or profile_data.get("category") or "-"
        created = profile_data.get("created_at") or "-"
        identifier_title_key = "dashboard.stats.broadcaster_id" if platform == "twitch" else "dashboard.stats.room_id"
        self.channel_badges["identifier"]["title"].setText(self.i18n.get(identifier_title_key))

        self._set_channel_badge("followers", followers_text)
        self._set_channel_badge("created", created)
        self._set_channel_badge("category", category)
        self._set_channel_badge("identifier", str(identifier))

        if avatar_bytes:
            self.set_avatar_from_bytes(avatar_bytes)
        else:
            self._current_avatar_bytes = None
            self.platform_distribution_ring.set_avatar(None)

    def _set_channel_badge(self, badge_key: str, value: str):
        badge = self.channel_badges[badge_key]
        normalized_value = str(value or "-")
        badge["value"].set_value(normalized_value)

    def _clear_channel_badges(self):
        for badge in self.channel_badges.values():
            badge["value"].set_value("-")

    def _switch_channel_account(self):
        if not self.btn_switch_channel.isVisible():
            return
        target_platform = "twitch" if self._current_profile_platform == "kick" else "kick"
        self.channel_tab_changed.emit(target_platform)

    def update_analytics_summary(self, analytics: dict):
        if not analytics:
            return

        top_commands = analytics.get("top_commands", [])
        if getattr(self, "_rendered_top_commands", None) != top_commands:
            self._rendered_top_commands = list(top_commands)
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
                self.top_commands_container.addWidget(lbl_none)
            else:
                max_cnt = max((cmd.get("count", 1) for cmd in top_commands), default=1)
                usages_str = self.i18n.get("dashboard.analytics.usages")
                for idx, cmd in enumerate(top_commands):
                    row = QHBoxLayout()
                    row.setSpacing(Size.SPACING_MD)

                    lbl_rank = QLabel(f"#{idx + 1}")
                    lbl_rank.setProperty("role", "rank_number")

                    lbl_trigger = QLabel(cmd.get("trigger", ""))
                    lbl_trigger.setProperty("role", "body")

                    pbar = QProgressBar()
                    pbar.setProperty("role", "top_command_progress")
                    pbar.setTextVisible(False)
                    pbar.setRange(0, max_cnt)
                    pbar.setValue(cmd.get("count", 0))

                    lbl_cnt = QLabel(f"{cmd.get('count', 0)} {usages_str}")
                    lbl_cnt.setProperty("role", "caption")

                    row.addWidget(lbl_rank)
                    row.addWidget(lbl_trigger)
                    row.addWidget(pbar, stretch=1)
                    row.addWidget(lbl_cnt)
                    self.top_commands_container.addLayout(row)

        self.lbl_active_cmds_val.setText(str(analytics.get("active_commands", 0)))
        self.lbl_active_timers_val.setText(str(analytics.get("active_timers", 0)))
        self.lbl_active_rewards_val.setText(str(analytics.get("total_rewards", 0)))

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
            if error_msg:
                logger.warning("[DashboardView] Connection error: %s", error_msg)

    def update_profile_info(self, username: str, bio: str):
        self.lbl_welcome_channel_name.setText(username)
        self.lbl_welcome_channel_description.setText(bio)

    def update_stats(self, followers: str, room_id: str, category: str, _affiliate_text: str, _vods_text: str, created_at: str = "-"):
        self._set_channel_badge("followers", followers)
        self._set_channel_badge("identifier", room_id)
        self._set_channel_badge("category", category)
        self._set_channel_badge("created", created_at)

    def update_session_metrics(self, msg_count: int, cmd_count: int, timer_count: int, spam_count: int):
        total = msg_count + cmd_count + timer_count + spam_count
        metrics = [
            (self.card_msg_processed, msg_count, BrandColors.PURPLE),
            (self.card_cmd_executed, cmd_count, BrandColors.BLUE),
            (self.card_timers_sent, timer_count, BrandColors.GREEN),
            (self.card_spam_blocked, spam_count, BrandColors.RED),
        ]
        for card, count, _ in metrics:
            card.set_value(self._fmt_metric(count, total))

    def set_avatar_from_bytes(self, image_data: bytes):
        if getattr(self, "_current_avatar_bytes", None) == image_data:
            return
        self._current_avatar_bytes = image_data
        pixmap = create_circular_pixmap(
            image_data, target_size=PlatformDistributionRing.DEFAULT_AVATAR_SIZE
        )
        if not pixmap.isNull():
            self.platform_distribution_ring.set_avatar(pixmap)

    def reset_to_disconnected(self):
        self._current_avatar_bytes = None
        self.set_kick_status(connected=False)
        self.platform_distribution_ring.set_avatar(None)
        self.lbl_welcome_channel_name.setText(self.i18n.get("dashboard.welcome.unlinked_channel"))
        self.lbl_welcome_channel_description.setText(self.i18n.get("dashboard.welcome.unlinked_description"))
        self.btn_switch_channel.setVisible(False)
        self.btn_open_channel.setEnabled(False)
        self.btn_open_channel.setVisible(False)
        self._clear_channel_badges()

    def _on_reauth_kick_clicked(self):
        self.reauth_kick_requested.emit()

    def _on_reauth_twitch_clicked(self):
        self.reauth_twitch_requested.emit()

    def _on_open_channel_clicked(self):
        username = getattr(self, "_current_channel_username", "")
        platform = getattr(self, "_current_profile_platform", "kick")
        if username and username != "-":
            url = f"https://twitch.tv/{username}" if platform == "twitch" else f"https://kick.com/{username}"
            if hasattr(self, "browser_service") and self.browser_service and hasattr(self.browser_service, "open_url"):
                self.browser_service.open_url(url)
            else:
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl(url))

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
            items_html = "".join(f"<li style='margin-bottom: 3px;'>{self.i18n.get(key)}</li>" for key in kick_keys)
            title = self.i18n.get("dashboard.banner.title_kick")
            desc = self.i18n.get("dashboard.banner.desc_kick")
            self.lbl_warn_text_kick.setText(
                f"<div style='line-height: 135%;'>"
                f"<div style='font-size: 13px; font-weight: 700; color: {Palette.NEUTRAL_050}; margin-bottom: 2px;'>{title}</div>"
                f"<div style='font-size: 12px; color: {Palette.NEUTRAL_400}; margin-bottom: 5px;'>{desc}</div>"
                f"<ul style='margin-top: 0px; margin-bottom: 2px; padding-left: 18px; font-size: 12px; color: {Palette.NEUTRAL_200};'>"
                f"{items_html}"
                f"</ul>"
                f"</div>"
            )
            self.banner_scopes_kick.setVisible(True)
        else:
            self.banner_scopes_kick.setVisible(False)

        if twitch_keys:
            items_html = "".join(f"<li style='margin-bottom: 3px;'>{self.i18n.get(key)}</li>" for key in twitch_keys)
            title = self.i18n.get("dashboard.banner.title_twitch")
            desc = self.i18n.get("dashboard.banner.desc_twitch")
            self.lbl_warn_text_twitch.setText(
                f"<div style='line-height: 135%;'>"
                f"<div style='font-size: 13px; font-weight: 700; color: {Palette.NEUTRAL_050}; margin-bottom: 2px;'>{title}</div>"
                f"<div style='font-size: 12px; color: {Palette.NEUTRAL_400}; margin-bottom: 5px;'>{desc}</div>"
                f"<ul style='margin-top: 0px; margin-bottom: 2px; padding-left: 18px; font-size: 12px; color: {Palette.NEUTRAL_200};'>"
                f"{items_html}"
                f"</ul>"
                f"</div>"
            )
            self.banner_scopes_twitch.setVisible(True)
        else:
            self.banner_scopes_twitch.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()

        if hasattr(self, "welcome_content_layout"):
            welcome_direction = (
                QBoxLayout.Direction.TopToBottom if width < 900
                else QBoxLayout.Direction.LeftToRight
            )
            if self.welcome_content_layout.direction() != welcome_direction:
                self.welcome_content_layout.setDirection(welcome_direction)

        banner_dir = QBoxLayout.Direction.TopToBottom if width < 480 else QBoxLayout.Direction.LeftToRight
        align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop if width < 480 else Qt.AlignmentFlag.AlignVCenter

        if hasattr(self, 'banner_layout_kick'):
            if self.banner_layout_kick.direction() != banner_dir:
                self.banner_layout_kick.setDirection(banner_dir)
            if self.lbl_warn_text_kick.alignment() != align:
                self.lbl_warn_text_kick.setAlignment(align)

        if hasattr(self, 'banner_layout_twitch'):
            if self.banner_layout_twitch.direction() != banner_dir:
                self.banner_layout_twitch.setDirection(banner_dir)
            if self.lbl_warn_text_twitch.alignment() != align:
                self.lbl_warn_text_twitch.setAlignment(align)

        if hasattr(self, 'platforms_grid') and hasattr(self, 'platform_cards'):
            plat_cols = 1 if width < 620 else 2
            self._relayout_grid(self.platforms_grid, self.platform_cards, plat_cols, self._PLATFORM_CARDS_ATTR)

        if hasattr(self, 'session_grid') and hasattr(self, 'session_cards'):
            session_cols = 1 if width < 650 else (2 if width < 950 else 4)
            self._relayout_grid(self.session_grid, self.session_cards, session_cols, self._SESSION_CARDS_ATTR)

        if hasattr(self, "channel_badges_grid") and hasattr(self, "channel_badge_cards"):
            badge_cols = 1 if width < 650 else (2 if width < 950 else 4)
            self._relayout_grid(
                self.channel_badges_grid,
                self.channel_badge_cards,
                badge_cols,
                self._CHANNEL_BADGES_ATTR,
            )

        if hasattr(self, 'bottom_analytics_layout'):
            bottom_dir = QBoxLayout.Direction.TopToBottom if width < 1000 else QBoxLayout.Direction.LeftToRight
            if self.bottom_analytics_layout.direction() != bottom_dir:
                self.bottom_analytics_layout.setDirection(bottom_dir)
