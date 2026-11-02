# frontend\window\__init__.py

from typing import TYPE_CHECKING

_EXPORTS = {
    "MainWindowComposition": ".composition",
    "IntegrationsStatusPresenter": ".integrations_status",
    "DashboardStatusController": ".integrations_status",
    "SettingsIntegrationsView": ".integrations_status",
    "ConnectedPlatformsView": ".integrations_status",
    "MediaKeysHandler": ".media_keys",
    "ChatMessageRouter": ".messages",
    "NavigationCoordinator": ".navigation",
    "OverlayEventPresenter": ".overlay_events",
    "PlatformConnectionHandlers": ".platform_connections",
    "RewardRedemption": ".rewards",
    "RewardRedemptionOutcome": ".rewards",
    "RewardRedemptionHandler": ".rewards",
    "RewardRedemptionPresenter": ".rewards",
    "SchedulePresenter": ".schedule",
    "SessionMetrics": ".session_metrics",
    "ShutdownSequence": ".shutdown",
    "MainWindowShutdown": ".shutdown",
    "StartupSequencer": ".startup",
    "MainWindowStartup": ".startup",
    "TrayPresenter": ".tray",
    "AutoUpdateCoordinator": ".updates",
    "WhatsNewPresenter": ".whats_new",
    "WindowStateManager": ".window_state",
    "MainWindowWiring": ".wiring",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name in _EXPORTS:
        import importlib

        module = importlib.import_module(_EXPORTS[name], package=__name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from .composition import MainWindowComposition
    from .integrations_status import ConnectedPlatformsView, DashboardStatusController, IntegrationsStatusPresenter, SettingsIntegrationsView
    from .media_keys import MediaKeysHandler
    from .messages import ChatMessageRouter
    from .navigation import NavigationCoordinator
    from .overlay_events import OverlayEventPresenter
    from .platform_connections import PlatformConnectionHandlers
    from .rewards import RewardRedemption, RewardRedemptionHandler, RewardRedemptionOutcome, RewardRedemptionPresenter
    from .schedule import SchedulePresenter
    from .session_metrics import SessionMetrics
    from .shutdown import MainWindowShutdown, ShutdownSequence
    from .startup import MainWindowStartup, StartupSequencer
    from .tray import TrayPresenter
    from .updates import AutoUpdateCoordinator
    from .whats_new import WhatsNewPresenter
    from .window_state import WindowStateManager
    from .wiring import MainWindowWiring
