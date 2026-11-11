# backend\services\webhooks\webhook_dispatcher_service.py

import time
import uuid
from typing import Any, Callable, Iterable, Mapping

from backend.interfaces.i_webhooks import (
    CRITICAL_EVENT_TYPES,
    DeliveryJob,
    IEventSink,
    WebhookEndpointConfig,
    WebhookEvent,
)


class WebhookDispatcherService(IEventSink):
    def __init__(
        self,
        endpoints_provider: Callable[[], Iterable[WebhookEndpointConfig]],
        submit: Callable[[DeliveryJob, bool], bool],
        clock_ms: Callable[[], int] = lambda: int(time.time() * 1000),
    ) -> None:
        self._endpoints_provider = endpoints_provider
        self._submit = submit
        self._clock_ms = clock_ms

    def post_event(self, event_type: str, platform: str, data: Mapping[str, Any]) -> None:
        targets = [ep for ep in self._endpoints_provider() if ep.accepts(event_type, platform)]
        if not targets:
            return
        event = WebhookEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            platform=platform,
            timestamp_ms=self._clock_ms(),
            data=dict(data),
        )
        critical = event_type in CRITICAL_EVENT_TYPES
        for endpoint in targets:
            self._submit(DeliveryJob(endpoint, event), critical)
