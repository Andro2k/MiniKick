# frontend\views\__init__.py

from .base_view import BaseView
from .chat_view import ChatView
from .commands_view import CommandView
from .dashboard_view import DashboardView
from .logs_view import LogView
from .music_view import MusicView
from .rewards_view import RewardsView
from .settings_view import SettingsView
from .spam_view import SpamView
from .timers_view import TimersView
from .widgets_view import WidgetsView
from .schedule_view import ScheduleView
from .alerts_view import AlertsView

__all__ = [
    "BaseView",
    "ChatView",
    "CommandView",
    "DashboardView",
    "LogView",
    "MusicView",
    "RewardsView",
    "SettingsView",
    "SpamView",
    "TimersView",
    "WidgetsView",
    "ScheduleView",
    "AlertsView"
]
