# backend\controllers\__init__.py

from .alerts_controller import AlertsController
from .chat_controller import ChatController
from .command_controller import CommandController
from .dashboard_controller import DashboardController
from .log_controller import LogController
from .music_controller import MusicController
from .rewards_controller import RewardsController
from .schedule_controller import ScheduleController
from .settings_controller import SettingsController
from .spam_controller import SpamController
from .timer_controller import TimerController
from .update_controller import UpdateController
from .widget_controller import WidgetController

__all__ = [
    "AlertsController",
    "ChatController",
    "CommandController",
    "DashboardController",
    "LogController",
    "MusicController",
    "RewardsController",
    "ScheduleController",
    "SettingsController",
    "SpamController",
    "TimerController",
    "UpdateController",
    "WidgetController"
]
