from __future__ import annotations

from typing import TYPE_CHECKING

_EXPORTS = {
    "BaseView": ".base_view",
    "ChatView": ".chat_view",
    "CommandView": ".commands_view",
    "DashboardView": ".dashboard_view",
    "LogView": ".logs_view",
    "MusicView": ".music_view",
    "RewardsView": ".rewards_view",
    "SettingsView": ".settings_view",
    "TimersView": ".timers_view",
    "WidgetsView": ".widgets_view",
    "ScheduleView": ".schedule_view",
    "AlertsView": ".alerts_view",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(_EXPORTS[name], package=__name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


if TYPE_CHECKING:
    from .alerts_view import AlertsView
    from .base_view import BaseView
    from .chat_view import ChatView
    from .commands_view import CommandView
    from .dashboard_view import DashboardView
    from .logs_view import LogView
    from .music_view import MusicView
    from .rewards_view import RewardsView
    from .schedule_view import ScheduleView
    from .settings_view import SettingsView
    from .timers_view import TimersView
    from .widgets_view import WidgetsView
