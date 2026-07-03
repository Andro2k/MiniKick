# frontend\controllers\dashboard_controller.py

from PySide6.QtCore import QObject, Signal, Slot

class DashboardController(QObject):
    request_connection = Signal()
    auto_start_toggled = Signal(bool)
    reauth_requested = Signal()

    def __init__(self, view, avatar_service):
        super().__init__()
        self.view = view
        self.avatar_service = avatar_service
        self._connect_signals()

    def _connect_signals(self):
        self.view.connect_requested.connect(self.request_connection.emit)
        self.view.autostart_toggled.connect(self.auto_start_toggled.emit)
        self.view.reauth_requested.connect(self.reauth_requested.emit)
        self.avatar_service.avatar_downloaded.connect(self.view.set_avatar_from_bytes)

    @Slot(dict)
    def handle_connection_success(self, user_data: dict):
        self.view.update_connection_status(is_connecting=False)

        username = user_data.get("username", self.view.i18n.get("main.controllers.dashboard.unknown_user"))
        if user_data.get("is_verified", False):
            username += " ✓"
        bio = user_data.get("bio", self.view.i18n.get("main.controllers.dashboard.no_bio"))
        self.view.update_profile_info(username, bio)

        followers_str = f"{user_data.get('followers', 0):,}"
        room_str = str(user_data.get("room_id", "-"))
        category = user_data.get("last_category", self.view.i18n.get("main.controllers.dashboard.none"))
        
        is_affiliate = user_data.get("is_affiliate", False)
        affiliate_text = self.view.i18n.get("main.controllers.dashboard.affiliate") if is_affiliate else self.view.i18n.get("main.controllers.dashboard.not_affiliate")
        
        vods_enabled = user_data.get("vod_enabled", False)
        vods_text = self.view.i18n.get("common.status.yes") if vods_enabled else self.view.i18n.get("common.status.no")

        self.view.update_stats(followers_str, room_str, category, affiliate_text, vods_text)
        avatar_url = user_data.get("avatar_url", "")
        if avatar_url:
            self.avatar_service.fetch_avatar(avatar_url)

    @Slot()
    def handle_connecting_state(self):
        self.view.update_connection_status(is_connecting=True)

    @Slot(str)
    def handle_error_state(self, error_msg: str):
        self.view.update_connection_status(is_connecting=False, has_error=True, error_msg=error_msg)

    @Slot()
    def reset_to_disconnected(self):
        self.view.reset_to_disconnected()

    @Slot(bool)
    def evaluate_scopes(self, is_missing: bool):
        self.view.show_scope_warning(is_missing)