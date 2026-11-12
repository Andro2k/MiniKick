# resources\tests\test_webhook_event_adapter.py

from backend.models import AlertEvent, AlertType
from backend.services.chat import ChatMessageDTO
from backend.services.webhooks.webhook_event_adapter import WebhookEventAdapter


class RecordingSink:
    def __init__(self):
        self.events = []

    def post_event(self, event_type, platform, data):
        self.events.append((event_type, platform, dict(data)))


def _adapter():
    sink = RecordingSink()
    return WebhookEventAdapter(sink), sink


def test_alert_is_mapped_with_its_type_and_viewer_data():
    adapter, sink = _adapter()
    adapter.on_alert(AlertEvent("e1", "twitch", AlertType.SUB_GIFT, "viewer123", "Viewer123", "gg", 5, "1"))
    assert sink.events == [("sub_gift", "twitch", {"username": "Viewer123", "message": "gg", "amount": 5, "tier": "1"})]


def test_chat_message_becomes_chat_or_command():
    adapter, sink = _adapter()
    adapter.on_chat_message(ChatMessageDTO("viewer123", "hello", [], "", "m1", 7, platform="twitch"))
    adapter.on_chat_message(ChatMessageDTO("viewer123", "!song", [], "", "m2", 7, platform="kick", is_command=True))
    assert [(kind, platform) for kind, platform, _ in sink.events] == [("chat", "twitch"), ("command", "kick")]
    assert sink.events[0][2] == {"username": "viewer123", "message": "hello", "message_id": "m1"}


def test_reward_keeps_platform():
    adapter, sink = _adapter()
    adapter.on_reward("viewer123", "Hydrate!", "please", platform="twitch")
    assert sink.events == [("reward", "twitch", {"username": "viewer123", "title": "Hydrate!", "message": "please"})]


def test_song_changes_are_deduplicated_and_empty_songs_ignored():
    adapter, sink = _adapter()
    adapter.on_song_changed({})
    adapter.on_song_changed({"title": "Song", "artist": "Band"})
    adapter.on_song_changed({"title": "Song", "artist": "Band"})
    adapter.on_song_changed({"title": "Other", "artist": "Band"})
    assert [data["title"] for _, _, data in sink.events] == ["Song", "Other"]
    assert all(platform == "app" for _, platform, _ in sink.events)


def test_goal_progress_is_posted_once_per_state_change():
    adapter, sink = _adapter()
    goal = {"goal_id": "g1", "goal_type": "followers", "current": 236, "target": 300, "status": "active"}
    adapter.on_goal_progress(goal)
    adapter.on_goal_progress(dict(goal))
    adapter.on_goal_progress({**goal, "current": 237})
    assert [e[2]["current"] for e in sink.events] == [236, 237]
    assert sink.events[0] == ("goal", "kick", {
        "goal_type": "followers", "current": 236, "target": 300, "status": "active", "message": "Followers: 236 / 300",
    })
