# backend\interfaces\i_webhooks.py

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Protocol

CRITICAL_EVENT_TYPES = frozenset({"subscription", "resub", "sub_gift", "follow", "raid", "cheer", "reward"})
PLATFORM_APP = "app"
DEFAULT_PLATFORMS = frozenset({"kick", "twitch", PLATFORM_APP})


@dataclass(frozen=True, slots=True)
class WebhookEndpointConfig:
    endpoint_id: str
    name: str
    target_url: str
    formatter: str = "generic"
    events: frozenset[str] = frozenset()
    platforms: frozenset[str] = DEFAULT_PLATFORMS
    hmac_secret: str = ""
    enabled: bool = True

    def accepts(self, event_type: str, platform: str) -> bool:
        return self.enabled and event_type in self.events and platform in self.platforms


@dataclass(frozen=True, slots=True)
class WebhookEvent:
    event_id: str
    event_type: str
    platform: str
    timestamp_ms: int
    data: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeliveryJob:
    endpoint: WebhookEndpointConfig
    event: WebhookEvent
    attempt: int = 0

    def next_attempt(self) -> DeliveryJob:
        return replace(self, attempt=self.attempt + 1)


@dataclass(frozen=True, slots=True)
class DeliveryResponse:
    status_code: int = 0
    retry_after: float | None = None
    error: str = ""
    permanent: bool = False

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def retryable(self) -> bool:
        if self.ok or self.permanent:
            return False
        return self.status_code in (0, 408, 429) or self.status_code >= 500


class IEventSink(Protocol):
    def post_event(self, event_type: str, platform: str, data: Mapping[str, Any]) -> None: ...


class IPayloadFormatter(Protocol):
    def format(self, event: WebhookEvent) -> bytes: ...


class IWebhookTransport(Protocol):
    def post(self, url: str, headers: Mapping[str, str], body: bytes) -> DeliveryResponse: ...
