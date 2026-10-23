"""Lazy creation and controller attachment for main-window views."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from frontend.views import (
    AlertsView,
    ChatView,
    CommandView,
    LogView,
    MusicView,
    RewardsView,
    ScheduleView,
    SettingsView,
    TimersView,
    WidgetsView,
)

if TYPE_CHECKING:
    from frontend.main_window import MainWindowCore


class MainWindowViewFactory:
    """Create each navigation view once and connect it to its controller."""

    def __init__(self, window: MainWindowCore) -> None:
        self._window = window

    def get_or_create(self, view_name: str) -> QWidget | None:
        window = self._window
        if view_name in window._instantiated_views:
            return window._instantiated_views[view_name]

        view_widget: QWidget | None = None
        if view_name == "Stream Info":
            window.view_schedule = ScheduleView(window.i18n, parent=window.content_stack)
            window.content_stack.addWidget(window.view_schedule)
            window.schedule_controller.attach_view(window.view_schedule)
            view_widget = window.view_schedule
        elif view_name == "Chat":
            window.view_chat = ChatView(window.i18n, parent=window.content_stack)
            window.content_stack.addWidget(window.view_chat)
            window.view_chat.chat_overlay_url = window.overlay_server.get_chat_overlay_url()
            window.chat_controller.attach_view(window.view_chat)
            if hasattr(window.view_chat, "spam_panel"):
                window.spam_controller.attach_view(window.view_chat.spam_panel)
            view_widget = window.view_chat
        elif view_name == "Music":
            window.view_music = MusicView(
                window.i18n,
                music_overlay_url=window.overlay_server.get_music_overlay_url(),
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_music)
            window.music_controller.attach_view(window.view_music)
            view_widget = window.view_music
        elif view_name == "Triggers":
            window.view_rewards = RewardsView(
                window.i18n,
                overlay_url=window.overlay_server.get_overlay_url(),
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_rewards)
            window.view_rewards.refresh_rewards_requested.connect(
                window._fetch_api_rewards
            )
            window.rewards_controller.attach_view(window.view_rewards)
            view_widget = window.view_rewards
        elif view_name == "Comandos":
            window.view_commands = CommandView(window.i18n, parent=window.content_stack)
            window.content_stack.addWidget(window.view_commands)
            window.commands_controller.attach_view(window.view_commands)
            view_widget = window.view_commands
        elif view_name == "Widgets":
            window.view_widgets = WidgetsView(
                window.i18n,
                shoutout_overlay_url=window.overlay_server.get_shoutout_overlay_url(),
                death_overlay_url=window.overlay_server.get_death_overlay_url(),
                score_overlay_url=window.overlay_server.get_score_overlay_url(),
                explosion_overlay_url=window.overlay_server.get_explosion_overlay_url(),
                combo_overlay_url=window.overlay_server.get_combo_overlay_url(),
                poll_overlay_url=window.overlay_server.get_poll_overlay_url(),
                pinned_overlay_url=window.overlay_server.get_pinned_overlay_url(),
                chatters_overlay_url=window.overlay_server.get_chatters_overlay_url(),
                clock_overlay_url=window.overlay_server.get_clock_overlay_url(),
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_widgets)
            window.widgets_controller.attach_view(window.view_widgets)
            view_widget = window.view_widgets
        elif view_name == "Timers":
            window.view_timers = TimersView(window.i18n, parent=window.content_stack)
            window.content_stack.addWidget(window.view_timers)
            window.timers_controller.attach_view(window.view_timers)
            view_widget = window.view_timers
        elif view_name == "Settings":
            window.view_settings = SettingsView(
                window.i18n, parent=window.content_stack
            )
            window.content_stack.addWidget(window.view_settings)
            window.view_settings.twitch_integration_clicked.connect(
                window._on_twitch_integration_button_clicked
            )
            window.view_settings.youtube_integration_clicked.connect(
                window._on_youtube_integration_button_clicked
            )
            window.view_settings.tiktok_integration_clicked.connect(
                window._on_tiktok_integration_button_clicked
            )
            window.settings_controller.attach_view(window.view_settings)
            window._update_integrations_status_ui()
            view_widget = window.view_settings
        elif view_name == "Developer":
            window.view_logs = LogView(window.i18n, parent=window.content_stack)
            window.content_stack.addWidget(window.view_logs)
            window.logs_controller.attach_view(window.view_logs)
            view_widget = window.view_logs
        elif view_name == "Alerts":
            window.view_alerts = AlertsView(
                window.i18n,
                alerts_overlay_url=window.overlay_server.get_alerts_overlay_url(),
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_alerts)
            window.view_alerts.set_connected_platforms(
                window.get_connected_platforms()
            )
            window.view_alerts.connect_platform_requested.connect(
                window._handle_alert_platform_connect
            )
            window.alerts_controller.attach_view(window.view_alerts)
            view_widget = window.view_alerts

        if view_widget is not None:
            window._instantiated_views[view_name] = view_widget
            if window.content_stack.indexOf(view_widget) == -1:
                window.content_stack.addWidget(view_widget)

        return view_widget
