# backend\services\webhooks\webhook_sender.py

import time
from typing import Callable, Mapping

from backend.interfaces.i_webhooks import DeliveryJob, DeliveryResponse, IPayloadFormatter, IWebhookTransport
from backend.services.webhooks.webhook_signer import build_headers


class WebhookSender:
    def __init__(
        self,
        formatters: Mapping[str, IPayloadFormatter],
        transport: IWebhookTransport,
        clock_ms: Callable[[], int] = lambda: int(time.time() * 1000),
    ) -> None:
        self._formatters = formatters
        self._transport = transport
        self._clock_ms = clock_ms

    def send(self, job: DeliveryJob) -> DeliveryResponse:
        endpoint = job.endpoint
        formatter = self._formatters.get(endpoint.formatter)
        if formatter is None:
            return DeliveryResponse(error="unknown_formatter", permanent=True)
        body = formatter.format(job.event)
        headers = build_headers(job.event.event_id, body, endpoint.hmac_secret, self._clock_ms())
        return self._transport.post(endpoint.target_url, headers, body)
