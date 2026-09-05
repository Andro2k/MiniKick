# frontend\views\alerts_view.py

from typing import Dict, Tuple
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QBoxLayout
from PySide6.QtCore import Qt, Signal
from backend.models import AlertConfig
from frontend.widgets import BaseView, ModernButton, ModernCard
from frontend.common import get_pixmap_colored, COLOR_AMBER
from frontend.components.alerts import (
    ResponsiveStackedWidget,
    AlertVariantListItem,
    AlertsSidebarPanel,
    AlertEventCard,
    AlertsOverlayCard,
)

__all__ = [
    "AlertsView","AlertEventCard","AlertVariantListItem","AlertsSidebarPanel","AlertsOverlayCard","ResponsiveStackedWidget"
]

class LazyAlertCardsDict(dict):
    def __init__(self, view):
        super().__init__()
        self._view = view

    def __contains__(self, key):
        if dict.__contains__(self, key):
            return True
        if isinstance(key, tuple) and len(key) == 2:
            plat, at = key
            return plat in self._view._event_meta and at in self._view._event_meta[plat]
        return False

    def __getitem__(self, key):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        if isinstance(key, tuple) and len(key) == 2 and self.__contains__(key):
            return self._view._get_or_create_card(key[0], key[1])
        return dict.__getitem__(self, key)

class AlertsView(BaseView):
    config_changed = Signal(object)
    test_alert_requested = Signal(str, str)
    copy_url_requested = Signal()
    open_browser_requested = Signal()
    connect_platform_requested = Signal(str)
    view_shown = Signal()

    _KICK_EVENTS = [("follow", "user-check.svg"),("subscription", "crown.svg"),("resub", "star.svg"),("sub_gift", "box-multiple-2.svg"),("raid", "users.svg"),]
    _TWITCH_EVENTS = [("follow", "user-check.svg"),("subscription", "crown.svg"),("resub", "star.svg"),("sub_gift", "box-multiple-2.svg"),("raid", "users.svg"),("cheer", "chart-bubble.svg"),]

    def __init__(self, i18n, alerts_overlay_url: str = "", parent=None):
        super().__init__(
            i18n=i18n,
            title_key="alerts.header.title",
            subtitle_key="alerts.header.subtitle",
            parent=parent
        )
        self.alerts_overlay_url = alerts_overlay_url
        self._configs_cache: Dict[Tuple[str, str], AlertConfig] = {}
        self._event_meta: Dict[str, Dict[str, str]] = {}
        self.cards: Dict[Tuple[str, str], AlertEventCard] = LazyAlertCardsDict(self)
        self.sidebar_items: Dict[Tuple[str, str], AlertVariantListItem] = {}
        self.sidebars: Dict[str, AlertsSidebarPanel] = {}
        self.active_variant: Dict[str, str] = {"kick": "follow", "twitch": "follow"}
        self.connected_platforms: Dict[str, bool] = {}
        self._last_direction = None

        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def _setup_ui(self):
        self.overlay_card = AlertsOverlayCard(self.alerts_overlay_url, self.i18n, parent=self)
        self.overlay_card.copy_url_requested.connect(self.copy_url_requested.emit)
        self.overlay_card.open_browser_requested.connect(self.open_browser_requested.emit)

        self.edit_overlay_url = self.overlay_card.edit_overlay_url
        self.btn_copy_url = self.overlay_card.btn_copy_url
        self.btn_open_browser = self.overlay_card.btn_open_browser
        self.url_box = self.overlay_card.url_box

        self.main_layout.addWidget(self.overlay_card)
        self.main_layout.addSpacing(6)

        platform_row = QHBoxLayout()
        platform_row.setSpacing(8)

        self.btn_tab_kick = ModernButton(
            text=self.i18n.get("alerts.platforms.kick"),
            role="action_kick",
            icon_name="brand-kick.svg",
            icon_size=16,
            parent=self
        )
        self.btn_tab_kick.setFixedHeight(32)
        self.btn_tab_kick.clicked.connect(lambda: self._switch_platform("kick"))

        self.btn_tab_twitch = ModernButton(
            text=self.i18n.get("alerts.platforms.twitch"),
            role="action_outlined",
            icon_name="brand-twitch.svg",
            icon_size=16,
            parent=self
        )
        self.btn_tab_twitch.setFixedHeight(32)
        self.btn_tab_twitch.clicked.connect(lambda: self._switch_platform("twitch"))

        platform_row.addWidget(self.btn_tab_kick)
        platform_row.addWidget(self.btn_tab_twitch)
        platform_row.addStretch()

        self.main_layout.addLayout(platform_row)
        self.main_layout.addSpacing(6)

        # Disconnection Notice Banner
        self.notice_banner = ModernCard(parent=self, margin=10, spacing=8)
        self.notice_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.notice_layout.setContentsMargins(0, 0, 0, 0)
        self.notice_layout.setSpacing(10)

        self.lbl_notice_icon = QLabel(parent=self)
        self.lbl_notice_icon.setPixmap(get_pixmap_colored("alert-triangle.svg", COLOR_AMBER, size=20))

        notice_text_col = QVBoxLayout()
        notice_text_col.setContentsMargins(0, 0, 0, 0)
        notice_text_col.setSpacing(2)

        self.lbl_notice_title = QLabel(self.i18n.get("alerts.notice.disconnected_title"), parent=self)
        self.lbl_notice_title.setProperty("role", "h3")
        self.lbl_notice_title.setProperty("state", "warning")

        self.lbl_notice_msg = QLabel(parent=self)
        self.lbl_notice_msg.setProperty("role", "body")
        self.lbl_notice_msg.setWordWrap(True)

        notice_text_col.addWidget(self.lbl_notice_title)
        notice_text_col.addWidget(self.lbl_notice_msg)

        self.btn_notice_connect = ModernButton(
            text=self.i18n.get("alerts.notice.connect_btn").replace("{platform}", "Kick"),
            role="action_outlined",
            icon_name="plug.svg",
            icon_size=15,
            parent=self
        )
        self.btn_notice_connect.setFixedHeight(32)
        self.btn_notice_connect.clicked.connect(self._on_notice_connect_clicked)

        self.notice_layout.addWidget(self.lbl_notice_icon, alignment=Qt.AlignmentFlag.AlignTop)
        self.notice_layout.addLayout(notice_text_col, stretch=1)
        self.notice_layout.addWidget(self.btn_notice_connect, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.notice_banner.addLayout(self.notice_layout)
        self.notice_banner.setVisible(False)

        self.main_layout.addWidget(self.notice_banner)
        self.main_layout.addSpacing(6)

        self.stack = ResponsiveStackedWidget(parent=self)
        self.stack.setMinimumWidth(0)

        kick_page, self.kick_sidebar, self.kick_editor_stack, self.kick_columns = self._build_master_detail_page("kick", self._KICK_EVENTS)
        twitch_page, self.twitch_sidebar, self.twitch_editor_stack, self.twitch_columns = self._build_master_detail_page("twitch", self._TWITCH_EVENTS)

        self.sidebars["kick"] = self.kick_sidebar
        self.sidebars["twitch"] = self.twitch_sidebar

        self.stack.addWidget(kick_page)
        self.stack.addWidget(twitch_page)

        self.main_layout.addWidget(self.stack)

        self._select_variant("kick", "follow")
        self._update_platform_connection_ui()

    def _build_master_detail_page(self, platform: str, events: list[tuple[str, str]]) -> tuple[QWidget, AlertsSidebarPanel, ResponsiveStackedWidget, QBoxLayout]:
        page = QWidget()
        page_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)

        self._event_meta[platform] = dict(events)

        sidebar_panel = AlertsSidebarPanel(platform, events, self.i18n, parent=page)
        sidebar_panel.variant_selected.connect(lambda at, p=platform: self._select_variant(p, at))

        for at, item in sidebar_panel.items.items():
            self.sidebar_items[(platform, at)] = item

        editor_stack = ResponsiveStackedWidget(parent=page)
        editor_stack.setMinimumWidth(0)

        page_layout.addWidget(sidebar_panel, 0)
        page_layout.addWidget(editor_stack, 1)

        return page, sidebar_panel, editor_stack, page_layout

    def _get_or_create_card(self, platform: str, alert_type: str) -> AlertEventCard:
        key = (platform, alert_type)
        if dict.__contains__(self.cards, key):
            return dict.__getitem__(self.cards, key)

        icon_name = self._event_meta.get(platform, {}).get(alert_type, "user-check.svg")
        editor_stack = self.kick_editor_stack if platform == "kick" else self.twitch_editor_stack
        sidebar_panel = self.sidebars.get(platform)

        card = AlertEventCard(platform, alert_type, icon_name, self.i18n, parent=editor_stack)
        card.set_platform_connected(bool(self.connected_platforms.get(platform, False)))
        card.save_requested.connect(self.config_changed.emit)
        card.test_requested.connect(self.test_alert_requested.emit)
        if sidebar_panel:
            card.config_changed.connect(lambda cfg, at=alert_type, sb=sidebar_panel: sb.set_item_enabled_state(at, cfg.enabled))

        if key in self._configs_cache:
            card.load_config(self._configs_cache[key])

        editor_stack.addWidget(card)
        dict.__setitem__(self.cards, key, card)
        return card

    def _select_variant(self, platform: str, alert_type: str):
        self.active_variant[platform] = alert_type

        sidebar = self.sidebars.get(platform)
        if sidebar:
            sidebar.select_variant(alert_type)

        target_card = self._get_or_create_card(platform, alert_type)
        editor_stack = self.kick_editor_stack if platform == "kick" else self.twitch_editor_stack
        editor_stack.setCurrentWidget(target_card)

    def _switch_platform(self, platform: str):
        if platform == "kick":
            self.btn_tab_kick.setProperty("role", "action_kick")
            self.btn_tab_twitch.setProperty("role", "action_outlined")
            self.stack.setCurrentIndex(0)
            kick_active = self.active_variant.get("kick", "follow")
            self._select_variant("kick", kick_active)
        else:
            self.btn_tab_kick.setProperty("role", "action_outlined")
            self.btn_tab_twitch.setProperty("role", "action_twitch")
            self.stack.setCurrentIndex(1)
            twitch_active = self.active_variant.get("twitch", "follow")
            self._select_variant("twitch", twitch_active)

        for btn in (self.btn_tab_kick, self.btn_tab_twitch):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._update_platform_connection_ui()

    def _on_notice_connect_clicked(self):
        curr_plat = "kick" if self.stack.currentIndex() == 0 else "twitch"
        self.connect_platform_requested.emit(curr_plat)

    def set_connected_platforms(self, connected_platforms: Dict[str, bool]):
        self.connected_platforms = connected_platforms or {}
        self._update_platform_connection_ui()

    def _update_platform_connection_ui(self):
        curr_plat = "kick" if self.stack.currentIndex() == 0 else "twitch"
        is_connected = bool(self.connected_platforms.get(curr_plat, False))

        if not is_connected:
            plat_name = "Kick" if curr_plat == "kick" else "Twitch"
            msg_template = self.i18n.get("alerts.notice.disconnected_msg")
            self.lbl_notice_msg.setText(msg_template.replace("{platform}", plat_name))
            btn_template = self.i18n.get("alerts.notice.connect_btn")
            self.btn_notice_connect.setText(btn_template.replace("{platform}", plat_name))
            self.notice_banner.setVisible(True)
        else:
            self.notice_banner.setVisible(False)

        kick_connected = bool(self.connected_platforms.get("kick", False))
        twitch_connected = bool(self.connected_platforms.get("twitch", False))

        self.btn_tab_kick.setText(self.i18n.get("alerts.platforms.kick"))
        self.btn_tab_twitch.setText(self.i18n.get("alerts.platforms.twitch"))

        kick_tip = self.i18n.get("alerts.platforms.kick") if kick_connected else f"{self.i18n.get('alerts.platforms.kick')} - {self.i18n.get('alerts.status.platform_offline')}"
        twitch_tip = self.i18n.get("alerts.platforms.twitch") if twitch_connected else f"{self.i18n.get('alerts.platforms.twitch')} - {self.i18n.get('alerts.status.platform_offline')}"

        self.btn_tab_kick.setToolTip(kick_tip)
        self.btn_tab_twitch.setToolTip(twitch_tip)

        for (plat, _), card in self.cards.items():
            card.set_platform_connected(bool(self.connected_platforms.get(plat, False)))

    def set_overlay_url(self, url: str):
        self.alerts_overlay_url = url
        self.overlay_card.set_overlay_url(url)

    def populate_configs(self, configs: dict[tuple[str, str], AlertConfig]):
        self._configs_cache.update(configs)
        for (plat, a_type), cfg in configs.items():
            item = self.sidebar_items.get((plat, a_type))
            if item:
                item.set_enabled_state(cfg.enabled)
            card = self.cards.get((plat, a_type))
            if card:
                card.load_config(cfg)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()

        if hasattr(self, 'overlay_card'):
            url_dir = QBoxLayout.Direction.TopToBottom if width < 800 else QBoxLayout.Direction.LeftToRight
            self.overlay_card.set_responsive_direction(url_dir)

        if hasattr(self, 'notice_layout'):
            notice_dir = QBoxLayout.Direction.TopToBottom if width < 680 else QBoxLayout.Direction.LeftToRight
            if notice_dir != self.notice_layout.direction():
                self.notice_layout.setDirection(notice_dir)
                if hasattr(self, 'notice_banner'):
                    self.notice_banner.card_layout.invalidate()
                    self.notice_banner.updateGeometry()
                if hasattr(self, 'scroll_content'):
                    self.scroll_content.layout().invalidate()
                    self.scroll_content.updateGeometry()

        target_direction = QBoxLayout.Direction.TopToBottom if width < 800 else QBoxLayout.Direction.LeftToRight
        if target_direction != self._last_direction:
            self._last_direction = target_direction
            is_horizontal = (target_direction == QBoxLayout.Direction.LeftToRight)

            for page_layout, sidebar in (
                (getattr(self, 'kick_columns', None), getattr(self, 'kick_sidebar', None)),
                (getattr(self, 'twitch_columns', None), getattr(self, 'twitch_sidebar', None))
            ):
                if page_layout and sidebar:
                    page_layout.setDirection(target_direction)
                    sidebar.set_responsive_mode(is_horizontal)
                    if is_horizontal:
                        page_layout.setStretch(0, 0)
                        page_layout.setStretch(1, 1)
                    else:
                        page_layout.setStretch(0, 0)
                        page_layout.setStretch(1, 0)
