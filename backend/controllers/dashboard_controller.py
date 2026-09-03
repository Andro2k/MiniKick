# backend\controllers\dashboard_controller.py

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

    def __init__(self, view, avatar_service, db_manager=None):
        super().__init__()
        self.view = view
        self.avatar_service = avatar_service
        self.db_manager = db_manager
        if self.db_manager is None and avatar_service and hasattr(avatar_service, "storage"):
            self.db_manager = getattr(avatar_service.storage, "db_manager", None)

        self._profiles: dict[str, dict | None] = {plat: None for plat in SUPPORTED_PLATFORMS}
        self._avatars: dict[str, bytes | None] = {plat: None for plat in SUPPORTED_PLATFORMS}
        self._current_tab = "kick"
        self._view_connected = False
        self._service_connected = False

        self._connect_service_signals()
        if self.view is not None:
            self._connect_signals()
        self._load_cached_profiles_from_db()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self._sync_view_profile()

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
        self.view.autostart_toggled.connect(self.auto_start_toggled.emit)
        self.view.reauth_requested.connect(self.reauth_requested.emit)
        if hasattr(self.view, "reauth_kick_requested"):
            self.view.reauth_kick_requested.connect(self.reauth_kick_requested.emit)
        if hasattr(self.view, "reauth_twitch_requested"):
            self.view.reauth_twitch_requested.connect(self.reauth_twitch_requested.emit)
        if hasattr(self.view, "channel_tab_changed"):
            self.view.channel_tab_changed.connect(self._on_channel_tab_changed)

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
