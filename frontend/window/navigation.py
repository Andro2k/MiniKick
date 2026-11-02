# frontend\window\navigation.py

from __future__ import annotations
import time


class NavigationCoordinator:
    def __init__(self, window) -> None:
        self._window = window
        self._last_navigation_at: float | None = None

    def handle_navigation(self, view_name: str) -> None:
        w = self._window
        navigation_started = time.perf_counter()
        self._last_navigation_at = navigation_started
        w.logger.info("[User Action] Navigated to view: '%s'", view_name)
        target_view = self.get_or_create_view(view_name)
        if target_view:
            switch_started = time.perf_counter()
            w.content_stack.setCurrentWidget(target_view)
            hooks_started = time.perf_counter()
            if view_name == "Dashboard":
                w._update_dashboard_metrics(force_db_query=True)
            elif view_name == "Settings":
                w.platform_connections.update_integrations_status_ui()
            elif view_name == "Triggers":
                w.platform_connections.fetch_api_rewards()
            finished = time.perf_counter()
            w.logger.info(
                "[Perf/Navigation] Navigation to '%s' completed in %.2f ms (create=%.2f, switch=%.2f, hooks=%.2f)",
                view_name,
                (finished - navigation_started) * 1000,
                (switch_started - navigation_started) * 1000,
                (hooks_started - switch_started) * 1000,
                (finished - hooks_started) * 1000,
            )

    def get_or_create_view(self, view_name: str):
        return self._window._view_factory.get_or_create(view_name)

    def seconds_since_navigation(self) -> float:
        if self._last_navigation_at is None:
            return float("inf")
        return time.perf_counter() - self._last_navigation_at
