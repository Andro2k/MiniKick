# resources\tests\test_overlay_server_start.py
"""Pruebas del arranque del servidor de overlays cuando el puerto esta ocupado."""

import socket

from backend.services.overlay.overlay_manager import OverlayServerManager


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def test_start_reports_failure_when_port_is_busy():
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        manager = OverlayServerManager(port=blocker.getsockname()[1])

        assert manager.start() is False

    assert manager.is_running is False
    assert manager.start_error


def test_start_succeeds_on_free_port_and_clears_previous_error():
    manager = OverlayServerManager(port=_free_port())
    manager.start_error = "stale"

    try:
        assert manager.start() is True
        assert manager.is_running is True
        assert manager.start_error is None
    finally:
        manager.stop()
