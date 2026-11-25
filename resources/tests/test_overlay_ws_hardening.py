# resources\tests\test_overlay_ws_hardening.py
"""Pruebas de los limites del WebSocket de overlays: tamano de frame."""

import io
import struct
from unittest.mock import MagicMock

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
