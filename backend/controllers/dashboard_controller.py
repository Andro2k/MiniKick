# backend\controllers\dashboard_controller.py

import datetime
import logging
from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger("minikick.controllers.dashboard")

SUPPORTED_PLATFORMS: tuple[str, ...] = ("kick", "twitch", "youtube", "tiktok")

class DashboardController(QObject):
    request_connection = Signal()
    twitch_connect_requested = Signal()
    youtube_connect_requested = Signal()
    tiktok_connect_requested = Signal()
    auto_start_toggled = Signal(bool)
    reauth_requested = Signal()
    reauth_kick_requested = Signal()
    reauth_twitch_requested = Signal()

    def __init__(self, view, avatar_service, db_manager=None, widget_service=None, widgets_controller=None, toast_manager=None, i18n=None):
        super().__init__()
        self.view = view
        self.avatar_service = avatar_service
        self.db_manager = db_manager
        self.widget_service = widget_service
        self.toast = toast_manager
        from backend.services.system import TranslationService
        self.i18n = i18n or TranslationService()
        self._widgets_controller = None
        self._current_chatters_date = datetime.date.today().strftime("%Y-%m-%d")
        if self.db_manager is None and avatar_service and hasattr(avatar_service, "storage"):
            self.db_manager = getattr(avatar_service.storage, "db_manager", None)

        self._profiles: dict[str, dict | None] = {plat: None for plat in SUPPORTED_PLATFORMS}
        self._avatars: dict[str, bytes | None] = {plat: None for plat in SUPPORTED_PLATFORMS}
        self._current_tab = "kick"
        self._view_connected = False
        self._service_connected = False

        self.widgets_controller = widgets_controller
        self._connect_service_signals()
        if self.view is not None:
            self._connect_signals()
        self._load_cached_profiles_from_db()
        self._init_top_chatters()

    @property
    def widgets_controller(self):
        return self._widgets_controller

    @widgets_controller.setter
    def widgets_controller(self, controller):
        if self._widgets_controller == controller:
            return
        if self._widgets_controller:
            try:
                if hasattr(self._widgets_controller, "chatters_updated"):
                    self._widgets_controller.chatters_updated.disconnect(self._on_chatters_updated)
                if hasattr(self._widgets_controller, "widget_status_changed"):
                    self._widgets_controller.widget_status_changed.disconnect(self._on_widget_status_changed)
            except Exception:
                pass
        self._widgets_controller = controller
        if self._widgets_controller:
            if hasattr(self._widgets_controller, "chatters_updated"):
                self._widgets_controller.chatters_updated.connect(self._on_chatters_updated)
            if hasattr(self._widgets_controller, "widget_status_changed"):
                self._widgets_controller.widget_status_changed.connect(self._on_widget_status_changed)

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self._sync_view_profile()
            self._init_top_chatters()

    def _connect_service_signals(self):
        if self._service_connected or not self.avatar_service:
            return
        self._service_connected = True
        if hasattr(self.avatar_service, "avatar_ready"):
            self.avatar_service.avatar_ready.connect(self._on_avatar_ready)
        if hasattr(self.avatar_service, "avatar_downloaded"):
            self.avatar_service.avatar_downloaded.connect(self._on_avatar_downloaded)

    def _connect_signals(self):
        if not self.view or self._view_connected:
            return
        self._view_connected = True
        self.view.connect_requested.connect(self.request_connection.emit)
        self.view.twitch_connect_requested.connect(self.twitch_connect_requested.emit)
        self.view.youtube_connect_requested.connect(self.youtube_connect_requested.emit)
        self.view.tiktok_connect_requested.connect(self.tiktok_connect_requested.emit)
        self.view.reauth_requested.connect(self.reauth_requested.emit)
        if hasattr(self.view, "reauth_kick_requested"):
            self.view.reauth_kick_requested.connect(self.reauth_kick_requested.emit)
        if hasattr(self.view, "reauth_twitch_requested"):
            self.view.reauth_twitch_requested.connect(self.reauth_twitch_requested.emit)
        if hasattr(self.view, "channel_tab_changed"):
            self.view.channel_tab_changed.connect(self._on_channel_tab_changed)
        if hasattr(self.view, "top_chatters_date_changed"):
            self.view.top_chatters_date_changed.connect(self._on_top_chatters_date_changed)
        if hasattr(self.view, "activate_chatters_requested"):
            self.view.activate_chatters_requested.connect(self._on_activate_chatters_requested)

    def _sync_widget_active_state(self):
        is_active = True
        if self.widget_service and hasattr(self.widget_service, "get_widget"):
            w = self.widget_service.get_widget("chatters")
            is_active = bool(w.get("is_active", True)) if w else True
        if self.view and hasattr(self.view, "set_chatters_widget_active"):
            self.view.set_chatters_widget_active(is_active)

    def _init_top_chatters(self):
        if not self.view:
            return
        dates = self.get_available_chatter_dates()
        if hasattr(self.view, "populate_chatter_dates"):
            self.view.populate_chatter_dates(dates)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        self._current_chatters_date = today_str
        self._sync_widget_active_state()
        self.load_top_chatters(today_str)

    def get_available_chatter_dates(self) -> list[str]:
        if self.widget_service and hasattr(self.widget_service, "get_available_chatter_dates"):
            return self.widget_service.get_available_chatter_dates()
        return []

    def load_top_chatters(self, date_str: str | None = None) -> list[dict]:
        if not date_str:
            date_str = datetime.date.today().strftime("%Y-%m-%d")
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        chatters_list: list[dict] = []
        if (
            date_str == today_str
            and self.widgets_controller
            and hasattr(self.widgets_controller, "_chatters_counts")
            and self.widgets_controller._chatters_counts
        ):
            chatters_dict = self.widgets_controller._chatters_counts
            chatters_list = sorted(chatters_dict.values(), key=lambda x: int(x.get("count", 0)), reverse=True)
        elif self.widget_service and hasattr(self.widget_service, "load_daily_chatters"):
            chatters_dict = self.widget_service.load_daily_chatters(date_str)
            chatters_list = list(chatters_dict.values())

        total_messages = sum(int(c.get("count", 0)) for c in chatters_list)
        if self.view and hasattr(self.view, "render_top_chatters"):
            self.view.render_top_chatters(chatters_list, total_messages=total_messages)
        return chatters_list

    def _on_top_chatters_date_changed(self, date_str: str):
        self._current_chatters_date = date_str
        self.load_top_chatters(date_str)

    def _on_chatters_updated(self):
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        if self._current_chatters_date == today_str:
            self.load_top_chatters(today_str)

    def _on_widget_status_changed(self, widget_id: str, is_active: bool):
        if widget_id == "chatters":
            if self.view and hasattr(self.view, "set_chatters_widget_active"):
                self.view.set_chatters_widget_active(is_active)

    def _on_activate_chatters_requested(self):
        if self.widgets_controller and hasattr(self.widgets_controller, "set_widget_active"):
            success = self.widgets_controller.set_widget_active("chatters", True)
            if success:
                self._sync_widget_active_state()
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                self.load_top_chatters(today_str)
                if self.toast:
                    self.toast.show_toast(
                        title=self.i18n.get("dashboard.chatters.toast_activated_title"),
                        message=self.i18n.get("dashboard.chatters.toast_activated_desc"),
                        state="success",
                        tag="widget_chatters_activated"
                    )

    def _load_cached_profiles_from_db(self):
        if not self.db_manager:
            return
        try:
            cached = self.db_manager.load_all_channel_profiles()
            for plat, data in cached.items():
                if plat in self._profiles and data:
                    self._profiles[plat] = data
                    avatar_url = data.get("avatar_url", "")
                    if avatar_url and self.avatar_service:
                        self.avatar_service.fetch_avatar(avatar_url, tag=plat)

            connected = [p for p, d in self._profiles.items() if d is not None]
            if connected:
                self._current_tab = connected[0]
                self._sync_view_profile()
            logger.debug("[DashboardController] Loaded cached channel profiles: %s", list(cached.keys()))
        except Exception as e:
            logger.error("[DashboardController] Error loading cached channel profiles from db: %s", e)

    def set_kick_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        if self.view and hasattr(self.view, "set_kick_status"):
            self.view.set_kick_status(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)
        if not connected and not connecting and not self.db_manager:
            self.clear_channel_profile("kick")

    def set_twitch_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        if self.view and hasattr(self.view, "set_twitch_status"):
            self.view.set_twitch_status(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)
        if not connected and not connecting and not self.db_manager:
            self.clear_channel_profile("twitch")

    def set_youtube_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        if self.view and hasattr(self.view, "set_youtube_status"):
            self.view.set_youtube_status(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)
        if not connected and not connecting and not self.db_manager:
            self.clear_channel_profile("youtube")

    def set_tiktok_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        if self.view and hasattr(self.view, "set_tiktok_status"):
            self.view.set_tiktok_status(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)
        if not connected and not connecting and not self.db_manager:
            self.clear_channel_profile("tiktok")

    def update_platform_messages(self, kick: int, twitch: int, youtube: int, tiktok: int):
        if self.view and hasattr(self.view, "update_platform_messages"):
            self.view.update_platform_messages(kick=kick, twitch=twitch, youtube=youtube, tiktok=tiktok)

    def update_analytics_summary(self, analytics: dict):
        if self.view and hasattr(self.view, "update_analytics_summary"):
            self.view.update_analytics_summary(analytics)

    def update_next_schedule(self, schedule_text: str):
        if self.view and hasattr(self.view, "update_next_schedule"):
            self.view.update_next_schedule(schedule_text)

    def set_channel_profile(self, platform: str, profile_data: dict, save_db: bool = True):
        plat = platform.lower().strip()
        self._profiles[plat] = profile_data
        
        if save_db and self.db_manager:
            try:
                self.db_manager.save_channel_profile(plat, profile_data)
            except Exception as e:
                logger.error("[DashboardController] Error saving profile for platform '%s': %s", plat, e)

        connected_platforms = [p for p, data in self._profiles.items() if data is not None]
        if not self._profiles.get(self._current_tab) or len(connected_platforms) == 1:
            self._current_tab = plat

        avatar_url = profile_data.get("avatar_url", "")
        if avatar_url and self.avatar_service:
            self.avatar_service.fetch_avatar(avatar_url, tag=plat)

        self._sync_view_profile()
        logger.debug("[DashboardController] Updated channel profile for platform: %s", plat)

    def clear_channel_profile(self, platform: str):
        plat = platform.lower().strip()
        self._profiles[plat] = None
        self._avatars[plat] = None
        if self.db_manager:
            try:
                self.db_manager.delete_channel_profile(plat)
            except Exception as e:
                logger.error("[DashboardController] Error deleting profile for platform '%s': %s", plat, e)
        connected_platforms = [p for p, data in self._profiles.items() if data is not None]
        if connected_platforms:
            if not self._profiles.get(self._current_tab):
                self._current_tab = connected_platforms[0]
        else:
            self._current_tab = "kick"
        self._sync_view_profile()
        logger.debug("[DashboardController] Cleared channel profile for platform: %s", plat)

    def _on_channel_tab_changed(self, platform: str):
        plat = platform.lower().strip()
        if plat in self._profiles and self._profiles[plat]:
            self._current_tab = plat
            self._sync_view_profile()
            logger.debug("[DashboardController] Channel tab switched to: %s", plat)

    def _sync_view_profile(self):
        connected_platforms = [p for p, data in self._profiles.items() if data is not None]
        active_data = self._profiles.get(self._current_tab)
        
        if self.view and hasattr(self.view, "render_channel_profile"):
            avatar_bytes = self._avatars.get(self._current_tab)
            self.view.render_channel_profile(
                platform=self._current_tab,
                profile_data=active_data,
                connected_platforms=connected_platforms,
                avatar_bytes=avatar_bytes
            )

    def _on_avatar_ready(self, platform_or_tag: str, image_data: bytes):
        plat = platform_or_tag.lower().strip()
        if plat in self._avatars:
            self._avatars[plat] = image_data
            if plat == self._current_tab and self.view and hasattr(self.view, "set_avatar_from_bytes"):
                self.view.set_avatar_from_bytes(image_data)

    def _on_avatar_downloaded(self, image_data: bytes):
        if not self._avatars.get(self._current_tab):
            self._avatars[self._current_tab] = image_data
            if self.view and hasattr(self.view, "set_avatar_from_bytes"):
                self.view.set_avatar_from_bytes(image_data)

    @Slot(object)
    def handle_connection_success(self, user_data: dict):
        logger.info("[DashboardController] Connection successful. Updating view status.")
        self.view.update_connection_status(is_connecting=False)
        self.set_channel_profile("kick", user_data)

    @Slot()
    def handle_connecting_state(self):
        logger.debug("[DashboardController] Entering connecting state.")
        self.view.update_connection_status(is_connecting=True)

    @Slot(str)
    def handle_error_state(self, error_msg: str):
        logger.error("[DashboardController] Connection error: %s", error_msg)
        self.view.update_connection_status(is_connecting=False, has_error=True, error_msg=error_msg)

    @Slot()
    def reset_to_disconnected(self):
        logger.info("[DashboardController] Resetting to disconnected state.")
        self.clear_channel_profile("kick")
        self.view.reset_to_disconnected()

    @Slot(object)
    def evaluate_scopes(self, missing_scope_keys: object):
        has_missing = False
        if isinstance(missing_scope_keys, dict):
            has_missing = any(bool(v) for v in missing_scope_keys.values())
        elif isinstance(missing_scope_keys, (list, set)):
            has_missing = bool(missing_scope_keys)

        if has_missing:
            logger.warning("[DashboardController] Missing OAuth scopes detected: %s", missing_scope_keys)
        self.view.show_scope_warning(missing_scope_keys)
