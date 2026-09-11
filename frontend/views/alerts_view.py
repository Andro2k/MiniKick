# frontend\views\alerts_view.py

from typing import Dict, Tuple
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from backend.models import AlertConfig
from frontend.widgets import BaseView, ModernButton, ModernCard
from frontend.common import get_pixmap_colored, COLOR_AMBER, SPACING_2XS, SPACING_SM, SPACING_MD, SPACING_LG, MARGIN_NONE
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

    _TWITCH_EVENTS = [
        ("follow", "user-check.svg"),
        ("subscription", "crown.svg"),
        ("resub", "star.svg"),
        ("sub_gift", "gift-filled.svg"),
        ("raid", "users.svg"),
        ("cheer", "prism.svg"),
    ]

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
        self.active_variant: Dict[str, str] = {"twitch": "follow"}
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

        self.main_layout.addWidget(self.overlay_card, 0)
        self.main_layout.addSpacing(SPACING_SM)

        self.notice_banner = ModernCard(parent=self, margin=SPACING_MD, spacing=SPACING_SM)
        self.notice_banner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.notice_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.notice_layout.setContentsMargins(*MARGIN_NONE)
        self.notice_layout.setSpacing(SPACING_MD)

        self.lbl_notice_icon = QLabel(parent=self)
        self.lbl_notice_icon.setPixmap(get_pixmap_colored("alert-triangle-duotone.svg", COLOR_AMBER, size=20))

        notice_text_col = QVBoxLayout()
        notice_text_col.setContentsMargins(*MARGIN_NONE)
        notice_text_col.setSpacing(SPACING_2XS)

        self.lbl_notice_title = QLabel(self.i18n.get("alerts.notice.disconnected_title"), parent=self)
        self.lbl_notice_title.setProperty("role", "h3")
        self.lbl_notice_title.setProperty("state", "warning")

        self.lbl_notice_msg = QLabel(parent=self)
        self.lbl_notice_msg.setProperty("role", "body")
        self.lbl_notice_msg.setWordWrap(True)

        notice_text_col.addWidget(self.lbl_notice_title)
        notice_text_col.addWidget(self.lbl_notice_msg)

        self.btn_notice_connect = ModernButton(
            text=self.i18n.get("alerts.notice.connect_btn").replace("{platform}", "Twitch"),
            role="action_outlined",
            icon_name="plug.svg",
            icon_size=15,
            parent=self
        )
        self.btn_notice_connect.clicked.connect(self._on_notice_connect_clicked)

        self.notice_layout.addWidget(self.lbl_notice_icon, alignment=Qt.AlignmentFlag.AlignTop)
        self.notice_layout.addLayout(notice_text_col, stretch=1)
        self.notice_layout.addWidget(self.btn_notice_connect, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.notice_banner.addLayout(self.notice_layout)
        self.notice_banner.setVisible(False)

        self.main_layout.addWidget(self.notice_banner, 0)
        self.main_layout.addSpacing(SPACING_SM)

        self.stack = ResponsiveStackedWidget(parent=self)
        self.stack.setMinimumWidth(0)

        twitch_page, self.twitch_sidebar, self.twitch_editor_stack, self.twitch_columns = self._build_master_detail_page("twitch", self._TWITCH_EVENTS)
        self.sidebars["twitch"] = self.twitch_sidebar

        self.stack.addWidget(twitch_page)

        self.main_layout.addWidget(self.stack, 0)
        self.main_layout.addStretch(1)

        self._select_variant("twitch", "follow")
        self._update_platform_connection_ui()

    def _build_master_detail_page(self, platform: str, events: list[tuple[str, str]]) -> tuple[QWidget, AlertsSidebarPanel, ResponsiveStackedWidget, QBoxLayout]:
        page = QWidget()
        page_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, page)
        page_layout.setContentsMargins(*MARGIN_NONE)
        page_layout.setSpacing(SPACING_LG)

        self._event_meta[platform] = dict(events)

        sidebar_panel = AlertsSidebarPanel(platform, events, self.i18n, parent=page)
        sidebar_panel.variant_selected.connect(lambda at, p=platform: self._select_variant(p, at))
        sidebar_panel.variant_enabled_changed.connect(lambda at, enabled, p=platform: self._on_sidebar_variant_enabled_changed(p, at, enabled))

        for at, item in sidebar_panel.items.items():
            self.sidebar_items[(platform, at)] = item

        editor_stack = ResponsiveStackedWidget(parent=page)
        editor_stack.setMinimumWidth(0)

        page_layout.addWidget(sidebar_panel, 0)
        page_layout.addWidget(editor_stack, 1)

        return page, sidebar_panel, editor_stack, page_layout

    def _on_sidebar_variant_enabled_changed(self, platform: str, alert_type: str, enabled: bool):
        card = self._get_or_create_card(platform, alert_type)
        if card:
            card.save_enabled_change(enabled)

    def _get_or_create_card(self, platform: str, alert_type: str) -> AlertEventCard:
        key = (platform, alert_type)
        if dict.__contains__(self.cards, key):
            return dict.__getitem__(self.cards, key)

        icon_name = self._event_meta.get(platform, {}).get(alert_type, "user-check.svg")
        editor_stack = self.twitch_editor_stack
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
        self.twitch_editor_stack.setCurrentWidget(target_card)

    def _switch_platform(self, platform: str = "twitch"):
        self.stack.setCurrentIndex(0)
        twitch_active = self.active_variant.get("twitch", "follow")
        self._select_variant("twitch", twitch_active)
        self._update_platform_connection_ui()

    def _on_notice_connect_clicked(self):
        self.connect_platform_requested.emit("twitch")

    def set_connected_platforms(self, connected_platforms: Dict[str, bool]):
        self.connected_platforms = connected_platforms or {}
        self._update_platform_connection_ui()

    def _update_platform_connection_ui(self):
        is_connected = bool(self.connected_platforms.get("twitch", False))

        if not is_connected:
            msg_template = self.i18n.get("alerts.notice.disconnected_msg")
            self.lbl_notice_msg.setText(msg_template.replace("{platform}", "Twitch"))
            btn_template = self.i18n.get("alerts.notice.connect_btn")
            self.btn_notice_connect.setText(btn_template.replace("{platform}", "Twitch"))
            self.notice_banner.setVisible(True)
        else:
            self.notice_banner.setVisible(False)

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
            url_dir = QBoxLayout.Direction.TopToBottom if width < 900 else QBoxLayout.Direction.LeftToRight
            self.overlay_card.set_responsive_direction(url_dir)

        if hasattr(self, 'notice_layout'):
            notice_dir = QBoxLayout.Direction.TopToBottom if width < 900 else QBoxLayout.Direction.LeftToRight
            if notice_dir != self.notice_layout.direction():
                self.notice_layout.setDirection(notice_dir)
                if hasattr(self, 'notice_banner'):
                    self.notice_banner.card_layout.invalidate()
                    self.notice_banner.updateGeometry()
                if hasattr(self, 'scroll_content'):
                    self.scroll_content.layout().invalidate()
                    self.scroll_content.updateGeometry()

        target_direction = QBoxLayout.Direction.TopToBottom if width < 900 else QBoxLayout.Direction.LeftToRight
        if target_direction != self._last_direction:
            self._last_direction = target_direction
            is_horizontal = (target_direction == QBoxLayout.Direction.LeftToRight)

            if hasattr(self, 'twitch_columns') and hasattr(self, 'twitch_sidebar'):
                self.twitch_columns.setDirection(target_direction)
                self.twitch_sidebar.set_responsive_mode(is_horizontal)
                if is_horizontal:
                    self.twitch_columns.setStretch(0, 0)
                    self.twitch_columns.setStretch(1, 1)
                else:
                    self.twitch_columns.setStretch(0, 0)
                    self.twitch_columns.setStretch(1, 0)
