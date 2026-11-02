# frontend\window\platform_connections.py

from __future__ import annotations

from PySide6.QtCore import Slot

from backend.connections import LiveChatConnection
from frontend.dialogs import ModernConfirmDialog, TikTokConnectDialog, YouTubeConnectDialog


class PlatformConnectionHandlers:
    _LIVE_CHAT_DIALOGS = {
        "youtube": (YouTubeConnectDialog, "dialogs.unlink_youtube.title", "dialogs.unlink_youtube.desc"),
        "tiktok": (TikTokConnectDialog, "dialogs.unlink_tiktok.title", "dialogs.unlink_tiktok.desc"),
    }
    _LIVE_CHAT_TOASTS = {
        "youtube": (
            "main.toast.youtube_connected_title",
            "main.toast.youtube_connected_msg",
            "main.toast.youtube_disconnected_title",
            "main.toast.youtube_disconnected_msg",
        ),
        "tiktok": (
            "main.toast.tiktok_connected_title",
            "main.toast.tiktok_connected_msg",
            "main.toast.tiktok_disconnected_title",
            "main.toast.tiktok_disconnected_msg",
        ),
    }

    def __init__(self, window) -> None:
        self._window = window

    @Slot()
    def handle_auth_process(self, force: bool = False, *, startup: bool = False) -> None:
        w = self._window
        if not startup:
            w._startup_silent_connections.discard("kick")
        if w.twitch.is_auth_running:
            w.toast.show_toast(
                title=w.container.i18n.get("main.toast.auth_in_progress_title"),
                message=w.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning",
            )
            return
        if startup:
            w._startup_silent_connections.add("kick")
        w.kick.authenticate(force=force)

    def on_kick_api_changed(self, api) -> None:
        w = self._window
        self.evaluate_all_scopes()
        w.command_service.api_client = api
        w.spam_service.api_client = api
        w.timer_service.api_client = api
        w.command_service.reload_cache()
        w.spam_service.reload_filters()
        w.schedule_service.set_kick_client(api)
        w.schedule_presenter.start_worker()
        w.schedule_controller.fetch_current_info()

    def on_kick_connected(self, username: str, user_data: dict) -> None:
        w = self._window
        w.spam_service.broadcaster_id = user_data.get("broadcaster_id", 0)
        w.dashboard_controller.handle_connection_success(user_data)
        self.refresh_sidebar_profile()
        if not w._consume_startup_silent_connection("kick"):
            w.toast.show_toast(
                title=w.i18n.get("main.toast.kick_connected_title"),
                message=w.i18n.get("main.toast.kick_connected_msg").replace("{username}", username),
                state="success",
            )
        self.fetch_api_rewards()

    @Slot()
    def fetch_api_rewards(self) -> None:
        w = self._window
        w.kick.fetch_rewards()
        if w.container.twitch_auth_manager.is_authenticated():
            w.twitch.fetch_rewards()

    @Slot(str)
    def handle_rewards_error(self, error_msg: str) -> None:
        w = self._window
        err_template = w.i18n.get("main.logs.api_error")
        w.logger.error(err_template.replace("{error}", error_msg))

    def handle_incoming_alert(self, alert_event) -> None:
        self._window.container.alert_service.process_event(alert_event)

    @Slot()
    def handle_twitch_auth_process(self, force: bool = False) -> None:
        w = self._window
        w._startup_silent_connections.discard("twitch")
        if w.kick.is_auth_running or w.twitch.is_auth_running:
            w.toast.show_toast(
                title=w.container.i18n.get("main.toast.auth_in_progress_title"),
                message=w.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning",
            )
            return
        w.twitch.authenticate(force=force)

    def on_twitch_browser_auth_opening(self) -> None:
        w = self._window
        w.toast.show_toast(
            title=w.container.i18n.get("main.toast.twitch_auth_title"),
            message=w.container.i18n.get("main.toast.twitch_auth_opening"),
            state="info",
        )

    def on_twitch_auth_failed(self, error: str) -> None:
        w = self._window
        if w._is_shutting_down:
            return
        w.toast.show_toast(
            title=w.container.i18n.get("main.toast.twitch_auth_error_title"),
            message=error,
            state="danger",
        )

    def on_twitch_api_changed(self, api) -> None:
        self._window.spam_service.twitch_api = api

    def on_twitch_chat_worker_changed(self, worker) -> None:
        w = self._window
        w.command_service.twitch_worker = worker
        w.spam_service.twitch_worker = worker

    def on_twitch_error(self, error_msg: str) -> None:
        w = self._window
        if w._is_shutting_down:
            return
        w.toast.show_toast(
            title=w.container.i18n.get("common.status.error"),
            message=error_msg,
            state="danger",
        )

    def on_twitch_connected(self, username: str, broadcaster_id: str, profile: dict) -> None:
        w = self._window
        if broadcaster_id:
            w.spam_service.twitch_broadcaster_id = broadcaster_id
        self.refresh_sidebar_profile()
        w.schedule_service.set_twitch_client(w.twitch.api, broadcaster_id)
        w.schedule_controller.fetch_current_info()
        w.rewards_controller.set_twitch_context(
            w.container.twitch_auth_manager,
            w.twitch.api,
            broadcaster_id,
        )
        if profile:
            w.dashboard_controller.set_channel_profile("twitch", profile)
        self.evaluate_all_scopes()
        if not w._consume_startup_silent_connection("twitch"):
            w.toast.show_toast(
                title=w.container.i18n.get("main.toast.twitch_connected_title"),
                message=w.container.i18n.get("main.toast.twitch_connected_msg").replace("{username}", username),
                state="success",
            )

    def refresh_sidebar_profile(self) -> None:
        w = self._window
        online_str = w.i18n.get("common.status.online")
        if w.kick.is_connected and w.kick.username:
            w.sidebar.update_profile_info(w.kick.username, online_str)
        elif w.twitch.is_connected and w.twitch.channel:
            w.sidebar.update_profile_info(w.twitch.channel, online_str)
        else:
            w.sidebar.reset_profile_info()

    def on_twitch_disconnected(self) -> None:
        w = self._window
        w.spam_service.twitch_broadcaster_id = ""
        w.dashboard_controller.clear_channel_profile("twitch")
        w.rewards_controller.clear_platform_rewards("twitch")
        self.refresh_sidebar_profile()
        w.toast.show_toast(
            title=w.container.i18n.get("main.toast.twitch_disconnected_title"),
            message=w.container.i18n.get("main.toast.twitch_disconnected_msg"),
            state="info",
        )
        self.evaluate_all_scopes()

    def update_integrations_status_ui(self) -> None:
        self._window.integrations_status.refresh()

    def get_connected_platforms(self) -> dict[str, bool]:
        return self._window.connection_hub.get_connected_platforms()

    def get_message_profile(self, platform: str) -> tuple[str, str]:
        w = self._window
        if platform == "kick":
            return w.kick.username, w.kick.avatar_url
        if platform == "twitch":
            return w.twitch.channel, w.twitch.avatar_url
        return "", ""

    def on_live_chat_button_clicked(self, chat: LiveChatConnection) -> None:
        w = self._window
        dialog_class, unlink_title_key, unlink_desc_key = self._LIVE_CHAT_DIALOGS[chat.platform_id]
        if chat.is_connected:
            w.logger.info("[User Action] Requested disconnecting %s", chat.log_name)
            dialog = ModernConfirmDialog(
                w.i18n,
                w,
                title_text=w.i18n.get(unlink_title_key),
                body_text=w.i18n.get(unlink_desc_key),
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                w._startup_silent_connections.discard(chat.platform_id)
                chat.disconnect_channel()
            return

        dialog = dialog_class(w.i18n, initial_target=chat.saved_target(), parent=w)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        target = "" if dialog.is_cleared() else dialog.get_target()
        if target:
            w._startup_silent_connections.discard(chat.platform_id)
            chat.connect_channel(target)
        else:
            chat.forget_channel()

    def on_live_chat_connecting(self, chat: LiveChatConnection) -> None:
        w = self._window
        set_status = getattr(w.dashboard_controller, f"set_{chat.platform_id}_status")
        set_status(connected=False, connecting=True)

    def on_live_chat_connected(self, chat: LiveChatConnection, display_name: str) -> None:
        w = self._window
        if w._consume_startup_silent_connection(chat.platform_id):
            return
        title_key, message_key, _, _ = self._LIVE_CHAT_TOASTS[chat.platform_id]
        w.toast.show_toast(
            title=w.i18n.get(title_key),
            message=w.i18n.get(message_key).replace("{target}", display_name),
            state="success",
        )

    def on_live_chat_disconnected(self, chat: LiveChatConnection) -> None:
        w = self._window
        _, _, title_key, message_key = self._LIVE_CHAT_TOASTS[chat.platform_id]
        w.toast.show_toast(
            title=w.i18n.get(title_key),
            message=w.i18n.get(message_key),
            state="info",
        )

    def on_live_chat_error(self, error_msg: str, is_offline: bool) -> None:
        w = self._window
        w.toast.show_toast(
            title=w.i18n.get("common.status.offline" if is_offline else "common.status.error"),
            message=error_msg,
            state="warning" if is_offline else "danger",
        )

    @Slot()
    def on_twitch_integration_button_clicked(self) -> None:
        w = self._window
        if w.twitch.is_connected:
            w.logger.info("[User Action] Requested unlinking Twitch account")
            dialog = ModernConfirmDialog(
                w.i18n,
                w,
                title_text=w.i18n.get("dialogs.unlink_twitch.title"),
                body_text=w.i18n.get("dialogs.unlink_twitch.desc"),
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                w.twitch.disconnect_account()
        else:
            self.handle_twitch_auth_process(force=False)

    @Slot()
    def evaluate_all_scopes(self) -> None:
        w = self._window
        missing_scopes = {
            "kick": w.kick_auth_manager.get_missing_scopes() if w.kick_auth_manager.is_authenticated() else [],
            "twitch": w.container.twitch_auth_manager.get_missing_scopes()
            if w.container.twitch_auth_manager.is_authenticated()
            else [],
        }
        w.dashboard_controller.evaluate_scopes(missing_scopes)

    @Slot()
    def force_reauth(self) -> None:
        w = self._window
        if w.container.twitch_auth_manager.has_missing_scopes():
            self.handle_reauth_twitch()
        elif w.kick_auth_manager.has_missing_scopes():
            self.handle_reauth_kick()

    @Slot()
    def handle_reauth_kick(self) -> None:
        self._window.kick.reauthenticate()

    def on_kick_reauth_ready(self) -> None:
        self._window.dashboard_controller.reset_to_disconnected()
        self.handle_auth_process(force=True)

    @Slot()
    def handle_reauth_twitch(self) -> None:
        w = self._window
        w.logger.info("[User Action] Requested renewal of Twitch permissions")
        self.handle_twitch_auth_process(force=True)

    @Slot()
    def handle_unlink_account(self) -> None:
        w = self._window
        if not w.kick.is_connected:
            self.handle_auth_process()
            return

        w.logger.info("[User Action] Requested unlinking Kick account")
        dialog = ModernConfirmDialog(
            w.i18n,
            w,
            title_text=w.i18n.get("dialogs.unlink.title"),
            body_text=w.i18n.get("dialogs.unlink.desc"),
        )
        if dialog.exec() == dialog.DialogCode.Accepted and w.kick.disconnect_account():
            w.toast.show_toast(
                title=w.i18n.get("main.toast.kick_disconnected_title"),
                message=w.i18n.get("main.toast.kick_disconnected_msg"),
                state="info",
            )

    def on_kick_disconnected(self) -> None:
        w = self._window
        w.dashboard_controller.clear_channel_profile("kick")
        w.rewards_controller.clear_platform_rewards("kick")
        self.refresh_sidebar_profile()
        self.evaluate_all_scopes()

    @Slot(str)
    def handle_alert_platform_connect(self, platform: str) -> None:
        if platform == "kick":
            self.handle_auth_process()
        elif platform == "twitch":
            self.handle_twitch_auth_process(force=False)
