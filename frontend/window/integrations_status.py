# frontend\window\integrations_status.py

import logging
import time
from collections.abc import Callable, Sequence
from typing import Protocol

from backend.connections.hub import ConnectionHub, IntegrationStatus
from frontend.window.session_metrics import SessionMetrics

logger = logging.getLogger("minikick.core")


class DashboardStatusController(Protocol):
    def set_kick_status(self, *, connected: bool, channel: str, msg_count: int) -> None: ...

    def set_twitch_status(self, *, connected: bool, channel: str, msg_count: int) -> None: ...

    def set_youtube_status(self, *, connected: bool, channel: str, msg_count: int) -> None: ...

    def set_tiktok_status(self, *, connected: bool, channel: str, msg_count: int) -> None: ...


class SettingsIntegrationsView(Protocol):
    def set_integrations_status(
        self,
        *,
        kick_connected: bool,
        kick_channel: str,
        twitch_connected: bool,
        twitch_channel: str,
        youtube_connected: bool,
        youtube_channel: str,
        tiktok_connected: bool,
        tiktok_channel: str,
    ) -> None: ...


class ConnectedPlatformsView(Protocol):
    def set_connected_platforms(self, connected_platforms: dict[str, bool]) -> None: ...


class IntegrationsStatusPresenter:
    _SLOW_STATUS_REFRESH_MS = 50.0

    def __init__(
        self,
        hub: ConnectionHub,
        dashboard_controller: DashboardStatusController,
        session_metrics: SessionMetrics,
        settings_view_provider: Callable[[], SettingsIntegrationsView | None],
        platform_views_provider: Callable[
            [], Sequence[ConnectedPlatformsView | None]
        ],
    ) -> None:
        self._hub = hub
        self._dashboard_controller = dashboard_controller
        self._session_metrics = session_metrics
        self._settings_view_provider = settings_view_provider
        self._platform_views_provider = platform_views_provider
        self._hub.status_changed.connect(self.refresh)

    def refresh(self) -> None:
        refresh_started = time.perf_counter()
        statuses = self._hub.get_integration_statuses()

        self._update_dashboard(statuses)
        dashboard_done = time.perf_counter()

        settings_view = self._settings_view_provider()
        if settings_view is not None:
            settings_view.set_integrations_status(
                kick_connected=statuses["kick"].connected,
                kick_channel=statuses["kick"].channel,
                twitch_connected=statuses["twitch"].connected,
                twitch_channel=statuses["twitch"].channel,
                youtube_connected=statuses["youtube"].connected,
                youtube_channel=statuses["youtube"].channel,
                tiktok_connected=statuses["tiktok"].connected,
                tiktok_channel=statuses["tiktok"].channel,
            )

        settings_view_done = time.perf_counter()
        connected_platforms = self._hub.get_connected_platforms()
        auth_done = time.perf_counter()
        for view in self._platform_views_provider():
            if view is not None:
                view.set_connected_platforms(connected_platforms)

        finished = time.perf_counter()
        total_ms = (finished - refresh_started) * 1000
        if total_ms >= self._SLOW_STATUS_REFRESH_MS:
            logger.info(
                "[Perf/Integrations] Status refresh took %.2f ms "
                "(dashboard=%.2f, settings_view=%.2f, auth=%.2f, views=%.2f)",
                total_ms,
                (dashboard_done - refresh_started) * 1000,
                (settings_view_done - dashboard_done) * 1000,
                (auth_done - settings_view_done) * 1000,
                (finished - auth_done) * 1000,
            )

    def _update_dashboard(
        self,
        statuses: dict[str, IntegrationStatus],
    ) -> None:
        dashboard = self._dashboard_controller
        metrics = self._session_metrics
        dashboard.set_kick_status(
            connected=statuses["kick"].connected,
            channel=statuses["kick"].channel,
            msg_count=metrics.platform_messages("kick"),
        )
        dashboard.set_twitch_status(
            connected=statuses["twitch"].connected,
            channel=statuses["twitch"].channel,
            msg_count=metrics.platform_messages("twitch"),
        )
        dashboard.set_youtube_status(
            connected=statuses["youtube"].connected,
            channel=statuses["youtube"].channel,
            msg_count=metrics.platform_messages("youtube"),
        )
        dashboard.set_tiktok_status(
            connected=statuses["tiktok"].connected,
            channel=statuses["tiktok"].channel,
            msg_count=metrics.platform_messages("tiktok"),
        )
