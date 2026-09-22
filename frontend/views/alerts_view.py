# frontend\views\alerts_view.py

from typing import Dict, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from backend.models import AlertConfig
from frontend.widgets import BaseView, ModernButton, ModernCard
from frontend.common import get_pixmap_colored, COLOR_AMBER, SPACING_2XS, SPACING_SM, SPACING_MD, MARGIN_NONE, MARGIN_MD
from frontend.components.alerts import (
    ResponsiveStackedWidget,
    AlertVariantsTabBar,
    AlertVariantTabPill,
    AlertEventCard,
    AlertsOverlayCard,
)
from frontend.dialogs import DuplicateAlertModal

__all__ = [
    "AlertsView",
    "AlertEventCard",
    "AlertVariantsTabBar",
    "AlertVariantTabPill",
    "AlertsOverlayCard",
    "ResponsiveStackedWidget"
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
        ("follow", "profile-tick-filled.svg"),
        ("subscription", "crown-filled.svg"),
        ("resub", "star-filled.svg"),
        ("sub_gift", "gift-filled.svg"),
        ("raid", "users-filled.svg"),
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
        self.sidebar_items: Dict[Tuple[str, str], AlertVariantTabPill] = {}
        self.sidebars: Dict[str, AlertVariantsTabBar] = {}
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

        self.notice_banner = ModernCard(parent=self, margin=MARGIN_MD, spacing=SPACING_SM)
        self.notice_banner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.notice_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.notice_layout.setContentsMargins(*MARGIN_NONE)
        self.notice_layout.setSpacing(SPACING_MD)

        self.lbl_notice_icon = QLabel(parent=self)
        self.lbl_notice_icon.setPixmap(get_pixmap_colored("alert-triangle-filled.svg", COLOR_AMBER, size=20))

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
            icon_name="plug-filled.svg",
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
        self.twitch_tab_bar = self.twitch_sidebar
        self.sidebars["twitch"] = self.twitch_sidebar

        self.stack.addWidget(twitch_page)

        self.main_layout.addWidget(self.stack, 0)
        self.main_layout.addStretch(1)

        self._select_variant("twitch", "follow")
        self._update_platform_connection_ui()

    def _build_master_detail_page(self, platform: str, events: list[tuple[str, str]]) -> tuple[QWidget, AlertVariantsTabBar, ResponsiveStackedWidget, QVBoxLayout]:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(*MARGIN_NONE)
        page_layout.setSpacing(SPACING_MD)

        self._event_meta[platform] = dict(events)

        tab_bar = AlertVariantsTabBar(platform, events, self.i18n, parent=page)
        tab_bar.variant_selected.connect(lambda at, p=platform: self._select_variant(p, at))
        tab_bar.variant_enabled_changed.connect(lambda at, enabled, p=platform: self._on_sidebar_variant_enabled_changed(p, at, enabled))

        for at, item in tab_bar.items.items():
            self.sidebar_items[(platform, at)] = item

        editor_stack = ResponsiveStackedWidget(parent=page)
        editor_stack.setMinimumWidth(0)

        page_layout.addWidget(tab_bar, 0)
        page_layout.addWidget(editor_stack, 1)

        return page, tab_bar, editor_stack, page_layout

    def _on_sidebar_variant_enabled_changed(self, platform: str, alert_type: str, enabled: bool):
        card = self._get_or_create_card(platform, alert_type)
        if card:
            card.save_enabled_change(enabled)

    def _get_or_create_card(self, platform: str, alert_type: str) -> AlertEventCard:
        key = (platform, alert_type)
        if dict.__contains__(self.cards, key):
            return dict.__getitem__(self.cards, key)

        icon_name = self._event_meta.get(platform, {}).get(alert_type, "profile-tick-filled.svg")
        editor_stack = self.twitch_editor_stack
        sidebar_panel = self.sidebars.get(platform)

        card = AlertEventCard(platform, alert_type, icon_name, self.i18n, parent=editor_stack)
        card.set_platform_connected(bool(self.connected_platforms.get(platform, False)))
        card.save_requested.connect(self.config_changed.emit)
        card.test_requested.connect(self.test_alert_requested.emit)
        card.duplicate_requested.connect(self._handle_duplicate_alert)
        if sidebar_panel:
            card.config_changed.connect(lambda cfg, at=alert_type, sb=sidebar_panel: sb.set_item_enabled_state(at, cfg.enabled))

        if key in self._configs_cache:
            card.load_config(self._configs_cache[key])

        editor_stack.addWidget(card)
        dict.__setitem__(self.cards, key, card)
        return card

    def _handle_duplicate_alert(self, source_cfg: AlertConfig):
        platform = source_cfg.platform
        source_event = source_cfg.alert_type
        events = self._TWITCH_EVENTS

        modal = DuplicateAlertModal(
            source_platform=platform,
            source_event=source_event,
            available_events=events,
            i18n=self.i18n,
            parent=self
        )
        if not modal.exec():
            return

        target_events, include_media, include_template = modal.get_selection()
        if not target_events:
            return

        for target_event in target_events:
            target_key = (platform, target_event)
            existing_target = self._configs_cache.get(target_key)
            target_card = self.cards.get(target_key)

            target_template = source_cfg.text_template if include_template else (
                existing_target.text_template if existing_target else (
                    target_card._current_config.text_template if target_card else f"¡{target_event}!"
                )
            )
            target_sound = source_cfg.sound_path if include_media else (
                existing_target.sound_path if existing_target else (
                    target_card._current_config.sound_path if target_card else ""
                )
            )
            target_media = source_cfg.media_path if include_media else (
                existing_target.media_path if existing_target else (
                    target_card._current_config.media_path if target_card else ""
                )
            )

            new_cfg = AlertConfig(
                platform=platform,
                alert_type=target_event,
                enabled=existing_target.enabled if existing_target else (target_card._current_config.enabled if target_card else True),
                sound_path=target_sound,
                media_path=target_media,
                text_template=target_template,
                duration_ms=source_cfg.duration_ms,
                sound_volume=source_cfg.sound_volume,
                tts_read=source_cfg.tts_read,
                layout=getattr(source_cfg, "layout", "above"),
                style=getattr(source_cfg, "style", "compact"),
                text_color=getattr(source_cfg, "text_color", "#FFFFFF"),
                highlight_color=getattr(source_cfg, "highlight_color", ""),
                font_family=getattr(source_cfg, "font_family", "Outfit"),
                font_size=getattr(source_cfg, "font_size", 24),
                text_align=getattr(source_cfg, "text_align", "center"),
                animation_in=getattr(source_cfg, "animation_in", "fade_in"),
                animation_in_duration=getattr(source_cfg, "animation_in_duration", 1.0),
                animation_out=getattr(source_cfg, "animation_out", "fade_out"),
                animation_out_duration=getattr(source_cfg, "animation_out_duration", 1.0),
                bg_color=getattr(source_cfg, "bg_color", "#121317"),
                bg_opacity=getattr(source_cfg, "bg_opacity", 88),
                border_radius=getattr(source_cfg, "border_radius", 20),
                padding_px=getattr(source_cfg, "padding_px", 24),
                spacing_px=getattr(source_cfg, "spacing_px", 16),
                box_shadow=getattr(source_cfg, "box_shadow", True),
                font_weight=getattr(source_cfg, "font_weight", "bold"),
                text_shadow=getattr(source_cfg, "text_shadow", True),
                card_width=getattr(source_cfg, "card_width", 560),
                card_height=getattr(source_cfg, "card_height", 0)
            )

            self._configs_cache[target_key] = new_cfg
            if target_card:
                target_card.load_config(new_cfg)
            self.config_changed.emit(new_cfg)

    def _select_variant(self, platform: str, alert_type: str):
        self.active_variant[platform] = alert_type

        sidebar = self.sidebars.get(platform)
        if sidebar:
            sidebar.select_variant(alert_type)

        target_card = self._get_or_create_card(platform, alert_type)
        self.twitch_editor_stack.setCurrentWidget(target_card)

    def _switch_platform(self, _platform: str = "twitch"):
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
            url_dir = QBoxLayout.Direction.TopToBottom if width < 1080 else QBoxLayout.Direction.LeftToRight
            self.overlay_card.set_responsive_direction(url_dir)

        if hasattr(self, 'notice_layout'):
            notice_dir = QBoxLayout.Direction.TopToBottom if width < 1080 else QBoxLayout.Direction.LeftToRight
            if notice_dir != self.notice_layout.direction():
                self.notice_layout.setDirection(notice_dir)
                if hasattr(self, 'notice_banner'):
                    self.notice_banner.card_layout.invalidate()
                    self.notice_banner.updateGeometry()
                if hasattr(self, 'scroll_content'):
                    self.scroll_content.layout().invalidate()
                    self.scroll_content.updateGeometry()

        target_direction = QBoxLayout.Direction.TopToBottom if width < 1080 else QBoxLayout.Direction.LeftToRight
        if target_direction != self._last_direction:
            self._last_direction = target_direction
            is_horizontal = (target_direction == QBoxLayout.Direction.LeftToRight)

            if hasattr(self, 'twitch_sidebar') and hasattr(self.twitch_sidebar, 'set_responsive_mode'):
                self.twitch_sidebar.set_responsive_mode(is_horizontal)
