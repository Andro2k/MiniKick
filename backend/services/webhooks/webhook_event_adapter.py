# backend\services\webhooks\webhook_event_adapter.py

from typing import Mapping

from backend.interfaces.i_webhooks import PLATFORM_APP, IEventSink
from backend.models import AlertEvent, AlertType
from backend.services.chat import ChatMessageDTO


class WebhookEventAdapter:
    def __init__(self, sink: IEventSink) -> None:
        self._sink = sink
        self._last_song: tuple[str, str] | None = None

    def on_alert(self, alert: AlertEvent) -> None:
        kind = alert.alert_type.value if isinstance(alert.alert_type, AlertType) else str(alert.alert_type)
        self._sink.post_event(kind, alert.platform, {
            "username": alert.display_name or alert.username,
            "message": alert.message,
            "amount": alert.amount,
            "tier": alert.tier,
        })

    def on_chat_message(self, dto: ChatMessageDTO) -> None:
        self._sink.post_event("command" if dto.is_command else "chat", dto.platform, {
            "username": dto.user,
            "message": dto.content,
            "message_id": dto.msg_id,
        })

    def on_reward(self, user: str, reward_name: str, message: str, platform: str = "kick") -> None:
        self._sink.post_event("reward", platform, {"username": user, "title": reward_name, "message": message})

    def on_song_changed(self, song: Mapping[str, str]) -> None:
        if not song:
            return
        key = (str(song.get("title", "")), str(song.get("artist", "")))
        if key == self._last_song:
            return
        self._last_song = key
        self._sink.post_event("music", PLATFORM_APP, {"title": key[0], "artist": key[1]})
