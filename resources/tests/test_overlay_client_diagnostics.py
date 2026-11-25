# resources\tests\test_overlay_client_diagnostics.py
"""Pruebas de los logs de diagnóstico del servidor de overlays."""

import logging
import os
from unittest.mock import MagicMock, patch

from backend.services.overlay.overlay_routes import OverlayRequestHandler


def _handler() -> OverlayRequestHandler:
    handler = OverlayRequestHandler.__new__(OverlayRequestHandler)
    handler.server = MagicMock()
    handler.send_error = MagicMock()
    return handler


def test_client_log_error_is_logged_as_warning_and_single_line():
    with patch("backend.services.overlay.overlay_routes.logger") as log:
        OverlayRequestHandler._log_client_message(
            "rewards", {"level": "error", "message": "play() rejected\nNotAllowedError"}
        )
    level, _fmt, topic, message = log.log.call_args.args
    assert level == logging.WARNING
    assert topic == "rewards"
    assert "\n" not in message


def test_client_log_info_level_and_message_truncated():
    with patch("backend.services.overlay.overlay_routes.logger") as log:
        OverlayRequestHandler._log_client_message("rewards", {"level": "info", "message": "x" * 1000})
    level, _fmt, _topic, message = log.log.call_args.args
    assert level == logging.INFO
    assert len(message) == 300


def test_media_request_for_missing_file_is_logged_and_refused(tmp_path):
    handler = _handler()
    missing = str(tmp_path / "gone.mp4")
    with patch("backend.services.overlay.overlay_routes.logger") as log:
        handler._handle_media_request({"path": [missing]})
    handler.send_error.assert_called_once()
    assert handler.send_error.call_args.args[0] == 404
    assert "gone.mp4" in str(log.warning.call_args)


def test_media_request_for_unregistered_file_is_logged_as_403(tmp_path):
    handler = _handler()
    handler.server.manager.allowed_media_files = set()
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x")
    with patch("backend.services.overlay.overlay_routes.logger") as log:
        handler._handle_media_request({"path": [str(media)]})
    assert handler.send_error.call_args.args[0] == 403
    assert "clip.mp4" in str(log.warning.call_args)


def test_served_media_logs_bytes_sent(tmp_path):
    handler = _handler()
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"abcdef")
    handler.headers = {}
    handler.wfile = MagicMock()
    handler.send_response = handler.send_header = handler.end_headers = MagicMock()
    handler.server.manager.allowed_media_files = {os.path.normcase(os.path.abspath(str(media)))}
    with patch("backend.services.overlay.overlay_routes._is_allowed_media_file", return_value=True), \
         patch("backend.services.overlay.overlay_routes.logger") as log:
        handler._handle_media_request({"path": [str(media)]})
    assert "served" in str(log.info.call_args)
    assert "sent=6/6" in (log.info.call_args.args[0] % log.info.call_args.args[1:])
