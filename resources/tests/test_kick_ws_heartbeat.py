# resources\tests\test_kick_ws_heartbeat.py

import socket
import time
from unittest.mock import MagicMock, patch
from backend.providers.chat.kick_ws_provider import KickWebSocketManager
from backend.utils.json_utils import fast_loads, fast_dumps


def test_pusher_connection_established_starts_watchdog_and_sets_activity_timeout():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mock_ws = MagicMock()

    payload = {"activity_timeout": 90}
    with patch.object(mgr, "_start_heartbeat_watchdog") as mock_start:
        mgr._handle_connection_established(payload, mock_ws)
        assert mgr._activity_timeout == 90
        assert mgr._last_activity_time > 0
        assert mgr._pending_ping_time == 0.0
        mock_start.assert_called_once_with(mock_ws)

def test_pusher_connection_established_fallback_default_timeout():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mock_ws = MagicMock()

    with patch.object(mgr, "_start_heartbeat_watchdog"):
        mgr._handle_connection_established({}, mock_ws)
        assert mgr._activity_timeout == 120

def test_raw_frame_updates_activity_time():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mgr._running = True
    mgr._pending_ping_time = 12345.0
    initial_time = 1000.0
    mgr._last_activity_time = initial_time

    mock_ws = MagicMock()
    raw = '{"event":"pusher:pong","data":{}}'
    mgr._on_raw_frame(mock_ws, raw)

    assert mgr._last_activity_time > initial_time
    assert mgr._pending_ping_time == 0.0

def test_pusher_ping_handler_sends_valid_pong_with_data():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mock_ws = MagicMock()

    mgr._handle_ping({}, mock_ws)
    mock_ws.send.assert_called_once()
    sent_payload = fast_loads(mock_ws.send.call_args[0][0])
    assert sent_payload.get("event") == "pusher:pong"
    assert sent_payload.get("data") == {}

def test_pusher_pong_handler_resets_pending_ping():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mgr._pending_ping_time = time.time()
    mock_ws = MagicMock()

    mgr._handle_pong({}, mock_ws)
    assert mgr._pending_ping_time == 0.0
    assert mgr._last_activity_time > 0

def test_heartbeat_watchdog_sends_proactive_ping_on_inactivity():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mgr._running = True
    mgr._activity_timeout = 60
    mgr._last_activity_time = time.time() - 35
    mgr._pending_ping_time = 0.0

    mock_ws = MagicMock()

    with patch.object(mgr._stop_heartbeat_event, "wait", return_value=True):
        now = time.time()
        ping_interval = min(mgr._activity_timeout // 2, 60)
        assert (now - mgr._last_activity_time) >= ping_interval

        mgr._pending_ping_time = now
        mock_ws.send(fast_dumps({"event": "pusher:ping", "data": {}}))

        sent_payload = fast_loads(mock_ws.send.call_args[0][0])
        assert sent_payload.get("event") == "pusher:ping"
        assert sent_payload.get("data") == {}
        assert mgr._pending_ping_time > 0

def test_heartbeat_watchdog_aborts_zombie_socket_on_pong_timeout():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    mgr._running = True
    mgr._pending_ping_time = time.time() - 35.0

    mock_ws = MagicMock()
    mock_sock = MagicMock()
    mock_sock.connected = True
    mock_ws.sock = mock_sock

    now = time.time()
    pong_timeout = 30.0

    if mgr._pending_ping_time > 0.0 and (now - mgr._pending_ping_time) > pong_timeout:
        mock_ws.sock.close()
        mock_ws.close()

    mock_sock.close.assert_called_once()
    mock_ws.close.assert_called_once()

def test_start_socket_configures_so_keepalive_and_nodelay():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))

    with patch("websocket.WebSocketApp") as mock_app_class:
        mock_app_instance = MagicMock()
        mock_app_class.return_value = mock_app_instance

        with patch.object(mock_app_instance, "run_forever") as mock_run_forever:
            def fake_run(**kwargs):
                sockopt = kwargs.get("sockopt", ())
                opts = {(opt[0], opt[1], opt[2]) for opt in sockopt}
                assert (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) in opts
                assert (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) in opts

            mock_run_forever.side_effect = fake_run
            mgr.start_socket(room_id=12345)

def test_stop_socket_stops_heartbeat_watchdog():
    mgr = KickWebSocketManager(cluster="us2", keys=("test_key",))
    with patch.object(mgr, "_stop_heartbeat_watchdog") as mock_stop_wd:
        mgr.stop_socket()
        assert mgr._running is False
        mock_stop_wd.assert_called_once()
