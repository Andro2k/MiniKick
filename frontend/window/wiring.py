from __future__ import annotations

from functools import partial

from backend.connections import LiveChatConnection


class MainWindowWiring:
    def __init__(self, window) -> None:
        self._window = window

    def connect_signals(self) -> None:
        w = self._window
        w.settings_controller.style_reload_requested.connect(w._apply_dynamic_theme)
        w.sidebar.view_selected.connect(w._handle_navigation)
        w.sidebar.section_viewed.connect(w.whats_new.on_section_viewed)
        w.dashboard_controller.request_connection.connect(w._handle_auth_process)
        w.dashboard_controller.twitch_connect_requested.connect(w._on_twitch_integration_button_clicked)
        w.dashboard_controller.youtube_connect_requested.connect(
            partial(w._on_live_chat_button_clicked, w.youtube)
        )
        w.dashboard_controller.tiktok_connect_requested.connect(
            partial(w._on_live_chat_button_clicked, w.tiktok)
        )
        self._wire_live_chat(w.youtube)
        self._wire_live_chat(w.tiktok)
        self._wire_twitch()
        self._wire_kick()
        w.dashboard_controller.reauth_requested.connect(w._force_reauth)
        w.dashboard_controller.reauth_kick_requested.connect(w._handle_reauth_kick)
        w.dashboard_controller.reauth_twitch_requested.connect(w._handle_reauth_twitch)
        w.chat_controller.tts_state_changed.connect(w._handle_chat_tts_state_changed)
        w.chat_controller.message_received.connect(w.overlay_server.trigger_chat_message)
        w.chat_controller.chat_overlay_config_changed.connect(
            w.overlay_server.trigger_chat_config_update
        )
        w.chat_controller.tts_ignored_users_changed.connect(
            w.widgets_controller.invalidate_ignored_bots_cache
        )
        w.chat_controller.message_received.connect(w.widgets_controller.handle_chat_message)
        w.music_controller.song_changed.connect(w.overlay_server.trigger_music_change)
        w.music_controller.song_changed.connect(w._handle_tray_song_changed)
        w.chat_controller.music_plugin_triggered.connect(w.music_controller.handle_music_plugin_command)
        w.chat_controller.widget_plugin_triggered.connect(w.widgets_controller.handle_widget_command)
        w.chat_controller.spam_blocked.connect(w.session_metrics.record_spam_blocked)
        w.session_metrics.refresh_requested.connect(w._refresh_dashboard_view)
        w.session_metrics.analytics_loaded.connect(w.dashboard_controller.update_analytics_summary)
        w.chat_controller.command_executed.connect(
            lambda *args: w._update_dashboard_metrics(force_db_query=True)
        )
        w.settings_controller.unlink_account_requested.connect(w._handle_unlink_account)
        w.settings_controller.check_update_requested.connect(w.handle_update_check)
        w.sidebar.update_requested.connect(w.handle_update_check)
        w.settings_controller.backup_restored.connect(w._on_backup_restored)
        w.q_log_handler.emitter.log_received.connect(w.logs_controller.process_incoming_log)
        w.avatar_service.avatar_downloaded.connect(w.sidebar.update_profile_avatar)

    def _wire_kick(self) -> None:
        w = self._window
        kick = w.kick
        kick.connecting.connect(w.dashboard_controller.handle_connecting_state)
        kick.error_reported.connect(w.dashboard_controller.handle_error_state)
        kick.api_changed.connect(w._on_kick_api_changed)
        kick.connected.connect(w._on_kick_connected)
        kick.disconnected.connect(w._on_kick_disconnected)
        kick.reauth_ready.connect(w._on_kick_reauth_ready)
        kick.message_received.connect(w._route_incoming_message)
        kick.poll_updated.connect(w._on_poll_updated)
        kick.poll_deleted.connect(w._on_poll_deleted)
        kick.pinned_created.connect(w._on_pinned_created)
        kick.pinned_deleted.connect(w._on_pinned_deleted)
        kick.reward_redeemed.connect(partial(w._on_reward_redeemed, platform="kick"))
        kick.rewards_fetched.connect(w.rewards_controller.update_rewards_list)
        kick.rewards_error.connect(w._handle_rewards_error)
        kick.timer_message_requested.connect(w._send_timer_message)

    def _wire_twitch(self) -> None:
        w = self._window
        twitch = w.twitch
        twitch.message_received.connect(w._route_incoming_message)
        twitch.browser_auth_opening.connect(w._on_twitch_browser_auth_opening)
        twitch.auth_failed.connect(w._on_twitch_auth_failed)
        twitch.session_started.connect(w._evaluate_all_scopes)
        twitch.api_changed.connect(w._on_twitch_api_changed)
        twitch.chat_worker_changed.connect(w._on_twitch_chat_worker_changed)
        twitch.connected.connect(w._on_twitch_connected)
        twitch.error_reported.connect(w._on_twitch_error)
        twitch.disconnected.connect(w._on_twitch_disconnected)
        twitch.reward_redeemed.connect(partial(w._on_reward_redeemed, platform="twitch"))
        twitch.alert_received.connect(w._handle_incoming_alert)
        twitch.rewards_fetched.connect(w.rewards_controller.update_rewards_list)

    def _wire_live_chat(self, chat: LiveChatConnection) -> None:
        w = self._window
        chat.connecting.connect(partial(w._on_live_chat_connecting, chat))
        chat.connected.connect(partial(w._on_live_chat_connected, chat))
        chat.disconnected.connect(partial(w._on_live_chat_disconnected, chat))
        chat.error_reported.connect(w._on_live_chat_error)
        chat.message_received.connect(w._route_incoming_message)
