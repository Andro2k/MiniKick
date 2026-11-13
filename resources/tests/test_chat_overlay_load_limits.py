# resources\tests\test_chat_overlay_load_limits.py

import json
import queue
import socket
import threading
from unittest.mock import MagicMock

import pytest
import websocket

from backend.controllers.widgets_controller import WidgetsController
from backend.services.chat.tts_service import TTSManager
from backend.services.overlay.overlay_manager import OverlayServerManager


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _bare_tts() -> TTSManager:
    tts = object.__new__(TTSManager)
    tts.text_queue = queue.Queue()
    tts.play_queue = queue.Queue()
    return tts


def test_tts_backlog_drops_the_oldest_pending_messages():
    tts = _bare_tts()
    for i in range(30):
        tts.play_queue.put((f"msg{i}", None, ""))

    tts._trim_backlog()

    remaining = []
    while not tts.play_queue.empty():
        remaining.append(tts.play_queue.get_nowait()[0])
    assert len(remaining) == TTSManager._MAX_PENDING_SPEECH - 1
    assert remaining[-1] == "msg29"
    assert "msg0" not in remaining


def test_tts_backlog_keeps_the_shutdown_sentinel():
    tts = _bare_tts()
    for _ in range(TTSManager._MAX_PENDING_SPEECH):
        tts.play_queue.put(None)

    tts._trim_backlog()

    assert tts.play_queue.qsize() == TTSManager._MAX_PENDING_SPEECH


def test_sse_broadcast_never_blocks_on_a_full_client_queue():
    manager = OverlayServerManager(port=_free_port())
    full = queue.Queue(maxsize=1)
    full.put({"old": True})
    manager.chat_clients.append(full)

    thread = threading.Thread(target=manager._broadcast, args=("chat_clients", "chat", {"a": 1}), daemon=True)
    thread.start()
    thread.join(1.0)

    assert not thread.is_alive()
    assert full.qsize() == 1


def test_overlay_websocket_answers_ping_with_pong():
    manager = OverlayServerManager(port=_free_port())
    manager.start()
    try:
        ws = websocket.create_connection(
            f"ws://127.0.0.1:{manager.port}/ws?topic=chat&token={manager.session_token}", timeout=5
        )
        ws.send(json.dumps({"type": "ping"}))
        ws.settimeout(3)
        assert json.loads(ws.recv()) == {"type": "pong"}
        ws.close()
    finally:
        manager.stop()


@pytest.fixture
def widgets(qapp):
    overlay = MagicMock()
    widget_service = MagicMock()
    configs = {
        "explosion": {"is_active": True, "config": {"min_emotes": 1, "particle_count": 15}},
        "combo": {"is_active": True, "config": {"min_combo": 3, "timeout_sec": 5.0}},
    }
    widget_service.get_widget.side_effect = lambda name: configs.get(name, {})
    controller = WidgetsController(
        MagicMock(), widget_service, MagicMock(), overlay_server=overlay,
        i18n=MagicMock(), ignored_users_provider=lambda: set(),
    )
    controller._record_chatter_message = lambda *args, **kwargs: None
    return controller, overlay


def _events(overlay, name):
    return [c.args[1] for c in overlay.trigger_widget_event.call_args_list if c.args[0] == name]


def test_combo_emits_a_single_event_per_message(widgets):
    controller, overlay = widgets

    controller.handle_chat_message("viewer", "[emote:1:Kappa]" * 5, "", [], "kick", "")

    combos = _events(overlay, "emote_combo")
    assert len(combos) == 1
    assert combos[0]["count"] == 5 and combos[0]["emote"] == "Kappa"


def test_explosion_events_are_rate_limited(widgets):
    controller, overlay = widgets

    controller.handle_chat_message("a", "[emote:1:Kappa]", "", [], "kick", "")
    controller.handle_chat_message("b", "[emote:1:Kappa]", "", [], "kick", "")
    assert len(_events(overlay, "emote_explosion")) == 1

    controller._last_explosion_at -= 1.0
    controller.handle_chat_message("c", "[emote:1:Kappa]", "", [], "kick", "")
    assert len(_events(overlay, "emote_explosion")) == 2
