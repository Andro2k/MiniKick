# backend\services\webhooks\webhook_transport.py

from typing import Mapping
from urllib.parse import urlsplit

import httpx

from backend.interfaces.i_webhooks import DeliveryResponse
from backend.utils import redact_secrets

DISCORD_DOMAINS = ("discord.com", "discordapp.com")

_CONNECT_TIMEOUT_S = 3.0
_REQUEST_TIMEOUT_S = 5.0


def is_discord_host(host: str) -> bool:
    host = host.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in DISCORD_DOMAINS)


def validate_target_url(url: str) -> str | None:
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return "invalid_url"
    if parts.scheme not in ("http", "https") or not host:
        return "invalid_url"
    if is_discord_host(host) and parts.scheme != "https":
        return "discord_requires_https"
    return None


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


class HttpWebhookTransport:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            follow_redirects=False,
            timeout=httpx.Timeout(_REQUEST_TIMEOUT_S, connect=_CONNECT_TIMEOUT_S),
        )

    def post(self, url: str, headers: Mapping[str, str], body: bytes) -> DeliveryResponse:
        problem = validate_target_url(url)
        if problem:
            return DeliveryResponse(error=problem, permanent=True)
        try:
            response = self._client.post(url, content=body, headers=dict(headers))
        except httpx.TimeoutException:
            return DeliveryResponse(error="timeout")
        except httpx.HTTPError as err:
            return DeliveryResponse(error=redact_secrets(f"{type(err).__name__}: {err}"))
        return DeliveryResponse(
            status_code=response.status_code,
            retry_after=_parse_retry_after(response.headers.get("Retry-After")),
        )

    def close(self) -> None:
        self._client.close()
