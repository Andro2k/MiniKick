# backend\controllers\__init__.py

from .alerts_controller import AlertsController
from .chat_controller import ChatController
from .commands_controller import CommandsController
from .dashboard_controller import DashboardController
from .logs_controller import LogsController
from .music_controller import MusicController
from .rewards_controller import RewardsController
from .schedule_controller import ScheduleController
from .settings_controller import SettingsController
from .spam_controller import SpamController
from .timers_controller import TimersController
from .updater_controller import UpdaterController
from .widgets_controller import WidgetsController

__all__ = [
    "AlertsController",
    "ChatController",
    "CommandsController",
    "DashboardController",
    "LogsController",
    "MusicController",
    "RewardsController",
    "ScheduleController",
    "SettingsController",
    "SpamController",
    "TimersController",
    "UpdaterController",
    "WidgetsController"
]
