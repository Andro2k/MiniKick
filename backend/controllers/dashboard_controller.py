# backend\controllers\dashboard_controller.py

from PySide6.QtCore import QObject, Signal, Slot

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
        self.db_manager = db_manager or (
            avatar_service.storage.db_manager
            if avatar_service and hasattr(avatar_service, "storage") and avatar_service.storage
            else None
        )
        self._profiles = {"kick": None, "twitch": None}
        self._avatars = {"kick": None, "twitch": None}
        self._current_tab = "kick"
        self._connect_signals()
        self._load_cached_profiles_from_db()

    def _connect_signals(self):
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
        if hasattr(self.avatar_service, "avatar_ready"):
            self.avatar_service.avatar_ready.connect(self._on_avatar_ready)
        self.avatar_service.avatar_downloaded.connect(self._on_avatar_downloaded)

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
        except Exception as e:
            pass

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

    def set_tiktok_status(self, connected: bool = False, channel: str = "", connecting: bool = False, msg_count: int = 0):
        if self.view and hasattr(self.view, "set_tiktok_status"):
            self.view.set_tiktok_status(connected=connected, channel=channel, connecting=connecting, msg_count=msg_count)

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
            self.db_manager.save_channel_profile(plat, profile_data)

        connected_platforms = [p for p, data in self._profiles.items() if data is not None]
        if not self._profiles.get(self._current_tab) or len(connected_platforms) == 1:
            self._current_tab = plat

        avatar_url = profile_data.get("avatar_url", "")
        if avatar_url and self.avatar_service:
            self.avatar_service.fetch_avatar(avatar_url, tag=plat)

        self._sync_view_profile()

    def clear_channel_profile(self, platform: str):
        plat = platform.lower().strip()
        self._profiles[plat] = None
        self._avatars[plat] = None
        if self.db_manager:
            self.db_manager.delete_channel_profile(plat)
        connected_platforms = [p for p, data in self._profiles.items() if data is not None]
        if connected_platforms:
            if not self._profiles.get(self._current_tab):
                self._current_tab = connected_platforms[0]
        else:
            self._current_tab = "kick"
        self._sync_view_profile()

    def _on_channel_tab_changed(self, platform: str):
        plat = platform.lower().strip()
        if plat in self._profiles and self._profiles[plat]:
            self._current_tab = plat
            self._sync_view_profile()

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
        self.view.update_connection_status(is_connecting=False)
        self.set_channel_profile("kick", user_data)

    @Slot()
    def handle_connecting_state(self):
        self.view.update_connection_status(is_connecting=True)

    @Slot(str)
    def handle_error_state(self, error_msg: str):
        self.view.update_connection_status(is_connecting=False, has_error=True, error_msg=error_msg)

    @Slot()
    def reset_to_disconnected(self):
        self.clear_channel_profile("kick")
        self.view.reset_to_disconnected()

    @Slot(object)
    def evaluate_scopes(self, missing_scope_keys: list):
        self.view.show_scope_warning(missing_scope_keys)
