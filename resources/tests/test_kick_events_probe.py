# resources\tests\test_kick_events_probe.py

import json

import websocket

from resources.tools import kick_events_probe as probe


class FakeWs:
    def __init__(self, frames):
        self._frames = list(frames)
        self.sent = []
        self.closed = False

    def settimeout(self, _value):
        pass

    def send(self, text):
        self.sent.append(json.loads(text))

    def recv(self):
        if not self._frames:
            raise websocket.WebSocketTimeoutException()
        item = self._frames.pop(0)
        if isinstance(item, BaseException):
            raise item
        return json.dumps(item)

    def close(self):
        self.closed = True


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        self.now += 0.5
        return self.now


def _listen(frames, duration=20, **kwargs):
    ws = FakeWs(frames)
    result = probe.listen("us2", "k", ["channel_1", "chatrooms.9.v2"], duration, ws_factory=lambda *_a, **_k: ws, clock=Clock(), **kwargs)
    return result, ws


def test_build_channels_skips_templates_missing_ids():
    assert probe.build_channels("9", None) == ["chatrooms.9.v2", "chatroom_9"]
    assert probe.build_channels(None, "1") == ["channel_1", "channel.1"]
    assert probe.build_channels("9", "1", ("chatrooms.{room}", "channel_1")) == [
        "chatrooms.9.v2", "chatroom_9", "channel_1", "channel.1", "chatrooms.9",
    ]


def test_suggest_type_prefers_gift_over_subscription():
    assert probe.suggest_type("App\\Events\\GiftedSubscriptionsEvent") == "sub_gift"
    assert probe.suggest_type("App\\Events\\SubscriptionEvent") == "subscription"
    assert probe.suggest_type("App\\Events\\FollowersUpdated") == "follow"
    assert probe.suggest_type("App\\Events\\Unknown") is None


def test_listen_catalogs_events_and_answers_ping():
    frames = [
        {"event": "pusher_internal:subscription_succeeded", "channel": "channel_1", "data": "{}"},
        {"event": "pusher:subscription_error", "channel": "chatrooms.9.v2", "data": {"message": "denied"}},
        {"event": "pusher:ping", "data": {}},
        {"event": "App\\Events\\FollowersUpdated", "channel": "channel_1", "data": json.dumps({"followersCount": 5, "username": "ana"})},
        {"event": "App\\Events\\FollowersUpdated", "channel": "channel_1", "data": json.dumps({"followersCount": 6})},
        {"event": "App\\Events\\ChatMessageEvent", "channel": "chatrooms.9.v2", "data": "{}"},
    ]
    seen = []
    result, ws = _listen(frames, on_new_event=seen.append)
    assert result["subscriptions"]["channel_1"] == "ok"
    assert result["subscriptions"]["chatrooms.9.v2"].startswith("error")
    assert {"event": "pusher:pong", "data": {}} in ws.sent
    follow = result["events"][0]
    assert (follow["count"], follow["possible_type"]) == (2, "follow")
    assert follow["shape"] == {"followersCount": "int", "username": "str"}
    assert result["chat_frames_ignored"] == 1 and len(seen) == 1 and ws.closed


def test_listen_can_include_chat_and_reports_closed_socket():
    frames = [{"event": "App\\Events\\ChatMessageEvent", "channel": "chatrooms.9.v2", "data": "{}"}, OSError("closed")]
    result, _ = _listen(frames, include_chat=True)
    assert len(result["events"]) == 1 and result["note"] == "socket cerrado: OSError"


def test_listen_keyboard_interrupt_returns_partial_report():
    frames = [{"event": "X\\FooEvent", "channel": "channel_1", "data": "{}"}, KeyboardInterrupt()]
    result, ws = _listen(frames)
    assert len(result["events"]) == 1 and result["note"] == "interrumpido por el usuario" and ws.closed
