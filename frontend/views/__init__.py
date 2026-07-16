# frontend\views\__init__.py

from .chat_view import ChatView
from .command_view import CommandView
from .dashboard_view import DashboardView
from .log_view import LogView
from .music_view import MusicView
from .network_view import NetworkView
from .rewards_view import RewardsView
from .settings_view import SettingsView
from .spam_view import SpamView
from .timers_view import TimersView

__all__ = [
    "ChatView",
    "CommandView",
    "DashboardView",
    "LogView",
    "MusicView",
    "NetworkView",
    "RewardsView",
    "SettingsView",
    "SpamView",
    "TimersView"
]
