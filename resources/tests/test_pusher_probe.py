# resources\tests\test_pusher_probe.py

import json
from unittest import mock
from resources.tools import pusher_probe


class FakeWs:
    def __init__(self, frame):
        self._frame = frame
        self.closed = False

    def recv(self):
        if isinstance(self._frame, Exception):
            raise self._frame
        return self._frame

    def close(self):
        self.closed = True

def _frame(event, data):
    return json.dumps({"event": event, "data": data})

def _probe(frame):
    ws = FakeWs(frame)
    with mock.patch.object(pusher_probe.websocket, "create_connection", return_value=ws):
        return pusher_probe.probe_key("us2", "k" * 20), ws

def test_accepted_key():
    (ok, detail), ws = _probe(_frame("pusher:connection_established", '{"socket_id":"1.2","activity_timeout":120}'))
    assert ok and "aceptada" in detail and ws.closed

def test_rejected_key_with_string_payload():
    (ok, detail), ws = _probe(_frame("pusher:error", '{"code":4001,"message":"App key does not exist"}'))
    assert not ok and "4001" in detail and "does not exist" in detail and ws.closed

def test_rejected_key_with_dict_payload():
    (ok, detail), _ = _probe(_frame("pusher:error", {"code": 4003, "message": "disabled"}))
    assert not ok and "4003" in detail

def test_unexpected_event_and_garbage():
    (ok, detail), _ = _probe(_frame("something:else", "{}"))
    assert not ok and "inesperada" in detail
    (ok2, detail2), _ = _probe("esto no es json")
    assert not ok2 and "sin respuesta válida" in detail2

def test_handshake_failure_is_reported_not_raised():
    with mock.patch.object(pusher_probe.websocket, "create_connection", side_effect=OSError("dns")):
        ok, detail = pusher_probe.probe_key("us2", "x")
    assert not ok and "no se pudo conectar" in detail

def test_main_exit_code_follows_the_preferred_key(capsys):
    config = pusher_probe.KICK_PUSHER.__class__(cluster="us2", keys=("NEWKEY0000000000", "OLDKEY0000000000"))
    answers = {"NEWKEY0000000000": (True, "aceptada"), "OLDKEY0000000000": (False, "rechazada")}
    with mock.patch.object(pusher_probe, "KICK_PUSHER", config), \
            mock.patch.object(pusher_probe, "probe_key", side_effect=lambda cluster, key, **_: answers[key]):
        assert pusher_probe.main([]) == 0
    out = capsys.readouterr().out
    assert "(preferida)" in out and "NEWK" in out

    answers["NEWKEY0000000000"] = (False, "rechazada")
    with mock.patch.object(pusher_probe, "KICK_PUSHER", config), \
            mock.patch.object(pusher_probe, "probe_key", side_effect=lambda cluster, key, **_: answers[key]):
        assert pusher_probe.main(["--json"]) == 1


class FakeListenWs:
    def __init__(self, frames):
        self._frames = list(frames)
        self.sent = []
        self.closed = False

    def send(self, payload):
        self.sent.append(json.loads(payload))

    def settimeout(self, _value):
        pass

    def recv(self):
        if not self._frames:
            raise OSError("closed")
        return self._frames.pop(0)

    def close(self):
        self.closed = True


def test_listen_stats_answers_ping_and_measures_transit():
    old = "2020-01-01T00:00:00+00:00"
    ws = FakeListenWs([
        _frame("pusher:ping", "{}"),
        _frame("App\\Events\\ChatMessageEvent", json.dumps({"created_at": old})),
    ])
    stats = pusher_probe.listen_stats("us2", "k", "1", wait=5, ws_factory=lambda *a, **k: ws)
    assert {"event": "pusher:pong", "data": {}} in ws.sent
    assert stats["frames"] == 2 and stats["chat_messages"] == 1 and stats["transit_over_5s"] == 1
    assert "socket cerrado" in stats["note"] and ws.closed


def test_discover_transports_lists_providers_and_checks_handshake():
    body = {"data": {"connections": [
        {"provider": "centrifugo", "credentials": {"url": "wss://realtime.x/connection/websocket"}},
        {"provider": "pusher", "credentials": {"app_key": "ABCD1234EFGH5678", "cluster": "us2"}},
    ]}}
    resp = mock.Mock(status_code=200, json=mock.Mock(return_value=body))
    with mock.patch.object(pusher_probe.requests, "post", return_value=resp), \
            mock.patch.object(pusher_probe, "check_handshake", return_value="ok (0.10s)"):
        providers, error = pusher_probe.discover_transports(123)
    assert error == "" and [p["provider"] for p in providers] == ["centrifugo", "pusher"]
    assert providers[0]["handshake"] == "ok (0.10s)" and providers[1]["key_preview"] == "ABCD…5678"


def test_discover_transports_reports_http_errors():
    with mock.patch.object(pusher_probe.requests, "post", return_value=mock.Mock(status_code=403)):
        providers, error = pusher_probe.discover_transports(1)
    assert providers == [] and "403" in error
