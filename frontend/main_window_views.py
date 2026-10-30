# frontend\main_window_views.py\\

from __future__ import annotations
import importlib
import logging
import time
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

_VIEW_EXPORTS = {
    "AlertsView": ".views.alerts_view",
    "ChatView": ".views.chat_view",
    "CommandView": ".views.commands_view",
    "LogView": ".views.logs_view",
    "MusicView": ".views.music_view",
    "RewardsView": ".views.rewards_view",
    "ScheduleView": ".views.schedule_view",
    "SettingsView": ".views.settings_view",
    "TimersView": ".views.timers_view",
    "WidgetsView": ".views.widgets_view",
}

def __getattr__(name: str):
    return _load_view_class(name)

def _load_view_class(name: str):
    cached_class = globals().get(name)
    if cached_class is not None:
        return cached_class

    module_name = _VIEW_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = importlib.import_module(module_name, package="frontend")
    view_class = getattr(module, name)
    globals()[name] = view_class
    return view_class

if TYPE_CHECKING:
    from frontend.views.alerts_view import AlertsView
    from frontend.views.chat_view import ChatView
    from frontend.views.commands_view import CommandView
    from frontend.views.logs_view import LogView
    from frontend.views.music_view import MusicView
    from frontend.views.rewards_view import RewardsView
    from frontend.views.schedule_view import ScheduleView
    from frontend.views.settings_view import SettingsView
    from frontend.views.timers_view import TimersView
    from frontend.views.widgets_view import WidgetsView
    from frontend.main_window import MainWindowCore

    _VIEW_CLASS_TYPES = (
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


class MainWindowViewFactory:
    def __init__(self, window: MainWindowCore) -> None:
        self._window = window

    def get_or_create(self, view_name: str) -> QWidget | None:
        window = self._window
        if view_name in window._instantiated_views:
            return window._instantiated_views[view_name]

        creation_started = time.perf_counter()
        view_widget: QWidget | None = None
        if view_name == "Stream Info":
            window.view_schedule = _load_view_class("ScheduleView")(
                window.i18n,
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_schedule)
            window.schedule_controller.attach_view(window.view_schedule)
            view_widget = window.view_schedule
        elif view_name == "Chat":
            window.view_chat = _load_view_class("ChatView")(
                window.i18n,
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_chat)
            window.view_chat.chat_overlay_url = window.overlay_server.get_chat_overlay_url()
            window.chat_controller.attach_view(window.view_chat)
            if hasattr(window.view_chat, "spam_panel"):
                window.spam_controller.attach_view(window.view_chat.spam_panel)
            view_widget = window.view_chat
        elif view_name == "Music":
            window.view_music = _load_view_class("MusicView")(
                window.i18n,
                music_overlay_url=window.overlay_server.get_music_overlay_url(),
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_music)
            window.music_controller.attach_view(window.view_music)
            view_widget = window.view_music
        elif view_name == "Triggers":
            window.view_rewards = _load_view_class("RewardsView")(
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
            window.view_commands = _load_view_class("CommandView")(
                window.i18n,
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_commands)
            window.commands_controller.attach_view(window.view_commands)
            view_widget = window.view_commands
        elif view_name == "Widgets":
            window.view_widgets = _load_view_class("WidgetsView")(
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
            window.view_timers = _load_view_class("TimersView")(
                window.i18n,
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_timers)
            window.timers_controller.attach_view(window.view_timers)
            view_widget = window.view_timers
        elif view_name == "Settings":
            window.view_settings = _load_view_class("SettingsView")(
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
            window.view_logs = _load_view_class("LogView")(
                window.i18n,
                parent=window.content_stack,
            )
            window.content_stack.addWidget(window.view_logs)
            window.logs_controller.attach_view(window.view_logs)
            view_widget = window.view_logs
        elif view_name == "Alerts":
            window.view_alerts = _load_view_class("AlertsView")(
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
            logger.info(
                "[Perf/Navigation] View '%s' created in %.2f ms",
                view_name,
                (time.perf_counter() - creation_started) * 1000,
            )

        return view_widget
