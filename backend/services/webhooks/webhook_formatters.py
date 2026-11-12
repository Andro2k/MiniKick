# backend\services\webhooks\webhook_formatters.py

from datetime import datetime, timezone

from backend.interfaces.i_webhooks import IPayloadFormatter, WebhookEvent
from backend.utils import fast_dumps

SCHEMA_VERSION = 1

_GREEN = 0x2ECC71
_GOLD = 0xF1C40F
_BLUE = 0x3498DB
_PURPLE = 0x9B59B6
_GRAY = 0x95A5A6

_EMBED_STYLES: dict[str, tuple[str, int]] = {
    "subscription": ("New subscription", _GREEN),
    "resub": ("Resubscription", _GREEN),
    "sub_gift": ("Gifted subscriptions", _GREEN),
    "cheer": ("Cheer", _GREEN),
    "reward": ("Reward redeemed", _GREEN),
    "follow": ("New follower", _GOLD),
    "raid": ("Incoming raid", _GOLD),
    "command": ("Command executed", _BLUE),
    "music": ("Now playing", _PURPLE),
    "goal": ("Goal progress", _GOLD),
    "test": ("Test ping", _BLUE),
    "chat": ("Chat message", _GRAY),
}
_DEFAULT_STYLE = ("MiniKick event", _GRAY)
_EXTRA_FIELDS = (("amount", "Amount"), ("tier", "Tier"), ("artist", "Artist"), ("status", "Status"))
_MAX_DESCRIPTION = 2000


class GenericJsonFormatter:
    def format(self, event: WebhookEvent) -> bytes:
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "id": event.event_id,
            "type": event.event_type,
            "platform": event.platform,
            "timestamp": event.timestamp_ms,
            "data": dict(event.data),
        }
        return fast_dumps(envelope).encode("utf-8")


class DiscordEmbedFormatter:
    def format(self, event: WebhookEvent) -> bytes:
        title, color = _EMBED_STYLES.get(event.event_type, _DEFAULT_STYLE)
        embed: dict = {
            "title": title,
            "color": color,
            "fields": self._fields(event),
            "timestamp": datetime.fromtimestamp(event.timestamp_ms / 1000, tz=timezone.utc).isoformat(),
            "footer": {"text": "MiniKick"},
        }
        description = self._description(event.data)
        if description:
            embed["description"] = description
        payload = {"username": "MiniKick", "allowed_mentions": {"parse": []}, "embeds": [embed]}
        return fast_dumps(payload).encode("utf-8")

    @staticmethod
    def _description(data) -> str:
        user = data.get("display_name") or data.get("username") or ""
        text = str(data.get("title") or data.get("message") or "")
        head = f"**{user}**" if user else ""
        if head and text:
            return f"{head}: {text}"[:_MAX_DESCRIPTION]
        return (head or text)[:_MAX_DESCRIPTION]

    @staticmethod
    def _fields(event: WebhookEvent) -> list[dict]:
        fields = [{"name": "Platform", "value": event.platform.capitalize() or "-", "inline": True}]
        for key, label in _EXTRA_FIELDS:
            value = event.data.get(key)
            if value not in (None, ""):
                fields.append({"name": label, "value": str(value), "inline": True})
        return fields


FORMATTER_REGISTRY: dict[str, IPayloadFormatter] = {
    "generic": GenericJsonFormatter(),
    "discord": DiscordEmbedFormatter(),
}
