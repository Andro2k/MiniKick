# resources\tests\test_overlay_widget_reconnect.py
"""Todo overlay que abre un WebSocket debe reconectar si el servidor se reinicia."""

from pathlib import Path

import pytest

_OVERLAYS = Path(__file__).resolve().parents[2] / "assets" / "overlays"
_SOURCES = sorted(
    p for p in [*_OVERLAYS.rglob("*.html"), *_OVERLAYS.rglob("*.js")]
    if "new WebSocket" in p.read_text(encoding="utf-8")
)


def test_overlays_with_websocket_were_found():
    assert _SOURCES


@pytest.mark.parametrize("source", _SOURCES, ids=lambda p: p.name)
def test_overlay_reconnects_after_close(source):
    text = source.read_text(encoding="utf-8")

    assert "onclose" in text
    assert "setTimeout" in text
