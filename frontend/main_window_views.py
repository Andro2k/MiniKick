# frontend/main_window_views.py

from __future__ import annotations
import importlib
import logging
import time
from typing import TYPE_CHECKING, Callable
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

    _USED_FOR_TYPING = (AlertsView, ChatView, CommandView, LogView, MusicView, 
                        RewardsView, ScheduleView, SettingsView, TimersView, WidgetsView)

class MainWindowViewFactory:
    def __init__(self, window: MainWindowCore) -> None:
        self._window = window
        self._view_builders: dict[str, Callable[[], QWidget]] = {
            "Stream Info": lambda: self._setup_generic_view("ScheduleView", "view_schedule", "schedule_controller"),
            "Comandos": lambda: self._setup_generic_view("CommandView", "view_commands", "commands_controller"),
            "Timers": lambda: self._setup_generic_view("TimersView", "view_timers", "timers_controller"),
            "Developer": lambda: self._setup_generic_view("LogView", "view_logs", "logs_controller"),
            "Chat": self._setup_chat_view,
            "Music": self._setup_music_view,
            "Triggers": self._setup_rewards_view,
            "Widgets": self._setup_widgets_view,
            "Settings": self._setup_settings_view,
            "Alerts": self._setup_alerts_view,
        }

    def get_or_create(self, view_name: str) -> QWidget | None:
        window = self._window
        if view_name in window._instantiated_views:
            return window._instantiated_views[view_name]

        builder = self._view_builders.get(view_name)
        if not builder:
            logger.warning("[Navigation] Intentó cargar una vista desconocida: %s", view_name)
            return None

        creation_started = time.perf_counter()
        
        view_widget = builder()

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

    def _setup_generic_view(self, class_name: str, attr_name: str, controller_name: str) -> QWidget:
        w = self._window
        view = _load_view_class(class_name)(w.i18n, parent=w.content_stack)
        setattr(w, attr_name, view)
        controller = getattr(w, controller_name)
        controller.attach_view(view)
        return view

    def _setup_chat_view(self) -> QWidget:
        w = self._window
        w.view_chat = _load_view_class("ChatView")(w.i18n, parent=w.content_stack)
        w.view_chat.chat_overlay_url = w.overlay_server.get_chat_overlay_url()
        w.chat_controller.attach_view(w.view_chat)
        if hasattr(w.view_chat, "spam_panel"):
            w.spam_controller.attach_view(w.view_chat.spam_panel)
        return w.view_chat

    def _setup_music_view(self) -> QWidget:
        w = self._window
        w.view_music = _load_view_class("MusicView")(w.i18n, music_overlay_url=w.overlay_server.get_music_overlay_url(), parent=w.content_stack)
        w.music_controller.attach_view(w.view_music)
        return w.view_music

    def _setup_rewards_view(self) -> QWidget:
        w = self._window
        w.view_rewards = _load_view_class("RewardsView")(w.i18n, overlay_url=w.overlay_server.get_overlay_url(), parent=w.content_stack)
        w.view_rewards.refresh_rewards_requested.connect(w._fetch_api_rewards)
        w.rewards_controller.attach_view(w.view_rewards)
        return w.view_rewards

    def _setup_widgets_view(self) -> QWidget:
        w = self._window
        w.view_widgets = _load_view_class("WidgetsView")(
            w.i18n,
            shoutout_overlay_url=w.overlay_server.get_shoutout_overlay_url(),
            death_overlay_url=w.overlay_server.get_death_overlay_url(),
            score_overlay_url=w.overlay_server.get_score_overlay_url(),
            explosion_overlay_url=w.overlay_server.get_explosion_overlay_url(),
            combo_overlay_url=w.overlay_server.get_combo_overlay_url(),
            poll_overlay_url=w.overlay_server.get_poll_overlay_url(),
            pinned_overlay_url=w.overlay_server.get_pinned_overlay_url(),
            chatters_overlay_url=w.overlay_server.get_chatters_overlay_url(),
            clock_overlay_url=w.overlay_server.get_clock_overlay_url(),
            parent=w.content_stack,
        )
        w.widgets_controller.attach_view(w.view_widgets)
        return w.view_widgets

    def _setup_settings_view(self) -> QWidget:
        w = self._window
        w.view_settings = _load_view_class("SettingsView")(w.i18n, parent=w.content_stack)
        w.view_settings.twitch_integration_clicked.connect(w._on_twitch_integration_button_clicked)
        w.view_settings.youtube_integration_clicked.connect(w._on_youtube_integration_button_clicked)
        w.view_settings.tiktok_integration_clicked.connect(w._on_tiktok_integration_button_clicked)
        w.settings_controller.attach_view(w.view_settings)
        w._update_integrations_status_ui()
        return w.view_settings

    def _setup_alerts_view(self) -> QWidget:
        w = self._window
        w.view_alerts = _load_view_class("AlertsView")(w.i18n, alerts_overlay_url=w.overlay_server.get_alerts_overlay_url(), parent=w.content_stack)
        w.view_alerts.set_connected_platforms(w.get_connected_platforms())
        w.view_alerts.connect_platform_requested.connect(w._handle_alert_platform_connect)
        w.alerts_controller.attach_view(w.view_alerts)
        return w.view_alerts