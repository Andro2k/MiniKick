# frontend\window\__init__.py

from typing import TYPE_CHECKING

_EXPORTS = {
    "MainWindowComposition": ".composition_coordinator",
    "IntegrationsStatusPresenter": ".integrations_protocols",
    "DashboardStatusController": ".integrations_protocols",
    "SettingsIntegrationsView": ".integrations_protocols",
    "ConnectedPlatformsView": ".integrations_protocols",
    "MediaKeysHandler": ".media_keys_handler",
    "ChatMessageRouter": ".messages_router",
    "NavigationCoordinator": ".navigation_coordinator",
    "OverlayEventPresenter": ".overlay_events_presenter",
    "PlatformConnectionHandlers": ".platform_connections_handler",
    "RewardRedemption": ".rewards_handler",
    "RewardRedemptionOutcome": ".rewards_handler",
    "RewardRedemptionHandler": ".rewards_handler",
    "RewardRedemptionPresenter": ".rewards_handler",
    "SchedulePresenter": ".schedule_presenter",
    "SessionMetrics": ".session_metrics_tracker",
    "ShutdownSequence": ".shutdown_coordinator",
    "MainWindowShutdown": ".shutdown_coordinator",
    "StartupSequencer": ".startup_coordinator",
    "MainWindowStartup": ".startup_coordinator",
    "TrayPresenter": ".tray_presenter",
    "AutoUpdateCoordinator": ".updates_coordinator",
    "WhatsNewPresenter": ".whats_new_presenter",
    "WindowStateManager": ".window_state_manager",
    "MainWindowWiring": ".wiring_coordinator",
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
    from .composition_coordinator import MainWindowComposition
    from .integrations_protocols import ConnectedPlatformsView, DashboardStatusController, IntegrationsStatusPresenter, SettingsIntegrationsView
    from .media_keys_handler import MediaKeysHandler
    from .messages_router import ChatMessageRouter
    from .navigation_coordinator import NavigationCoordinator
    from .overlay_events_presenter import OverlayEventPresenter
    from .platform_connections_handler import PlatformConnectionHandlers
    from .rewards_handler import RewardRedemption, RewardRedemptionHandler, RewardRedemptionOutcome, RewardRedemptionPresenter
    from .schedule_presenter import SchedulePresenter
    from .session_metrics_tracker import SessionMetrics
    from .shutdown_coordinator import MainWindowShutdown, ShutdownSequence
    from .startup_coordinator import MainWindowStartup, StartupSequencer
    from .tray_presenter import TrayPresenter
    from .updates_coordinator import AutoUpdateCoordinator
    from .whats_new_presenter import WhatsNewPresenter
    from .window_state_manager import WindowStateManager
    from .wiring_coordinator import MainWindowWiring
