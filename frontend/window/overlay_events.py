# frontend\window\overlay_events.py

from __future__ import annotations


class OverlayEventPresenter:
    def __init__(self, overlay_server) -> None:
        self._overlay_server = overlay_server

    def on_poll_updated(self, poll_data: dict) -> None:
        self._overlay_server.trigger_widget_event("poll_update", {"poll": poll_data})

    def on_poll_deleted(self) -> None:
        self._overlay_server.trigger_widget_event("poll_delete", {})

    def on_pinned_created(self, pinned_data: dict) -> None:
        self._overlay_server.trigger_widget_event("pinned_created", {"pinned": pinned_data})

    def on_pinned_deleted(self) -> None:
        self._overlay_server.trigger_widget_event("pinned_deleted", {})
