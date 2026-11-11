# backend\services\webhooks\webhook_management_service.py

import dataclasses
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from backend.config.webhook_endpoint_store import WebhookEndpointStore
from backend.interfaces.i_webhooks import (
    DEFAULT_PLATFORMS,
    PLATFORM_APP,
    DeliveryJob,
    WebhookEndpointConfig,
    WebhookEvent,
)
from backend.services.webhooks.webhook_sender import WebhookSender
from backend.services.webhooks.webhook_transport import validate_target_url

EVENT_TYPES = ("subscription", "resub", "sub_gift", "cheer", "follow", "raid", "reward", "command", "music", "chat")
PLATFORMS = ("kick", "twitch", PLATFORM_APP)
FORMATTERS = ("discord", "generic")
TEST_EVENT_TYPE = "test"


@dataclass(frozen=True, slots=True)
class PingResult:
    ok: bool
    status_code: int = 0
    latency_ms: int = 0
    error: str = ""


class WebhookManagementService:
    def __init__(
        self,
        store: WebhookEndpointStore,
        sender: WebhookSender,
        clock_ms: Callable[[], int] = lambda: int(time.time() * 1000),
    ) -> None:
        self._store = store
        self._sender = sender
        self._clock_ms = clock_ms

    @staticmethod
    def event_types() -> tuple[str, ...]:
        return EVENT_TYPES

    @staticmethod
    def platforms() -> tuple[str, ...]:
        return PLATFORMS

    @staticmethod
    def validate_url(url: str) -> str | None:
        return validate_target_url(url.strip())

    def list_endpoints(self) -> list[WebhookEndpointConfig]:
        return self._store.load_all()

    def get_endpoint(self, endpoint_id: str) -> WebhookEndpointConfig | None:
        return next((ep for ep in self._store.load_all() if ep.endpoint_id == endpoint_id), None)

    def save_endpoint(self, data: Mapping[str, Any]) -> WebhookEndpointConfig:
        endpoint = self._build(data)
        endpoints = self._store.load_all()
        for index, existing in enumerate(endpoints):
            if existing.endpoint_id == endpoint.endpoint_id:
                endpoints[index] = endpoint
                break
        else:
            endpoints.append(endpoint)
        self._store.save_all(endpoints)
        return endpoint

    def delete_endpoint(self, endpoint_id: str) -> bool:
        endpoints = self._store.load_all()
        remaining = [ep for ep in endpoints if ep.endpoint_id != endpoint_id]
        if len(remaining) == len(endpoints):
            return False
        self._store.save_all(remaining)
        return True

    def set_enabled(self, endpoint_id: str, enabled: bool) -> bool:
        endpoints = self._store.load_all()
        for index, endpoint in enumerate(endpoints):
            if endpoint.endpoint_id == endpoint_id:
                if endpoint.enabled == enabled:
                    return False
                endpoints[index] = dataclasses.replace(endpoint, enabled=enabled)
                self._store.save_all(endpoints)
                return True
        return False

    def send_test_ping(self, data: Mapping[str, Any]) -> PingResult:
        try:
            endpoint = self._build(data)
        except ValueError:
            return PingResult(ok=False, error="invalid_data")
        event = WebhookEvent(
            event_id=str(uuid.uuid4()),
            event_type=TEST_EVENT_TYPE,
            platform=PLATFORM_APP,
            timestamp_ms=self._clock_ms(),
            data={"username": "MiniKick", "message": "Test ping"},
        )
        started = time.perf_counter()
        try:
            response = self._sender.send(DeliveryJob(endpoint, event))
        except Exception as err:
            return PingResult(ok=False, error=type(err).__name__)
        latency_ms = int((time.perf_counter() - started) * 1000)
        error = "" if response.ok else (response.error or f"HTTP {response.status_code}")
        return PingResult(ok=response.ok, status_code=response.status_code, latency_ms=latency_ms, error=error)

    @staticmethod
    def _build(data: Mapping[str, Any]) -> WebhookEndpointConfig:
        name = str(data.get("name", "")).strip()
        target_url = str(data.get("target_url", "")).strip()
        formatter = str(data.get("formatter", "generic"))
        if not name or not target_url or formatter not in FORMATTERS:
            raise ValueError("incomplete endpoint data")
        if validate_target_url(target_url):
            raise ValueError("invalid target url")
        platforms = frozenset(p for p in data.get("platforms", DEFAULT_PLATFORMS) if p in PLATFORMS)
        events = frozenset(e for e in data.get("events", ()) if e in EVENT_TYPES)
        return WebhookEndpointConfig(
            endpoint_id=str(data.get("endpoint_id") or uuid.uuid4()),
            name=name,
            target_url=target_url,
            formatter=formatter,
            events=events,
            platforms=platforms,
            hmac_secret="" if formatter == "discord" else str(data.get("hmac_secret", "")).strip(),
            enabled=bool(data.get("enabled", True)),
        )
