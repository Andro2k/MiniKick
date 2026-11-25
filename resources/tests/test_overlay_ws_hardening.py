# resources\tests\test_overlay_ws_hardening.py
"""Pruebas de los limites del WebSocket de overlays: tamano de frame y topics."""

import io
import struct
from unittest.mock import MagicMock

from backend.services.overlay.overlay_manager import OverlayServerManager
from backend.services.overlay.overlay_routes import OverlayRequestHandler
from backend.services.overlay.overlay_ws_client import WebSocketClient


def _client(incoming: bytes) -> tuple[WebSocketClient, MagicMock]:
    handler = MagicMock()
    handler.rfile = io.BytesIO(incoming)
    handler.wfile = io.BytesIO()
    return WebSocketClient(handler, topic="chat", token="t"), handler


def test_read_frame_drops_client_announcing_oversized_payload():
    client, handler = _client(bytes([0x81, 127]) + struct.pack(">Q", 2**40))

    assert client.read_frame() is None
    assert client.closed is True
    handler.connection.shutdown.assert_called_once()


def test_read_frame_still_reads_small_masked_text_frame():
    mask = b"\x01\x02\x03\x04"
    body = bytes(b ^ mask[i % 4] for i, b in enumerate(b'{"type":"ping"}'))
    client, _handler = _client(bytes([0x81, 0x80 | len(body)]) + mask + body)

    assert client.read_frame() == '{"type":"ping"}'
    assert client.closed is False


def test_manager_knows_only_its_own_topics():
    manager = OverlayServerManager(port=0)

    assert manager.has_ws_topic("alerts") is True
    assert manager.has_ws_topic("nope") is False


def test_upgrade_with_unknown_topic_is_refused_before_switching_protocols():
    handler = OverlayRequestHandler.__new__(OverlayRequestHandler)
    handler.server = MagicMock()
    handler.server.manager.has_ws_topic.return_value = False
    handler.headers = {"Sec-WebSocket-Key": "abc"}
    handler.send_error = MagicMock()
    handler.send_response = MagicMock()

    handler._handle_websocket_upgrade({"topic": ["nope"]}, "tok")

    handler.send_error.assert_called_once()
    assert handler.send_error.call_args.args[0] == 400
    handler.send_response.assert_not_called()
    handler.server.manager.register_ws_client.assert_not_called()
