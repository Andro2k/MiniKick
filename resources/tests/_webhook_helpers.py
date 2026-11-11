# resources\tests\_webhook_helpers.py

from backend.interfaces.i_webhooks import DeliveryJob, WebhookEndpointConfig, WebhookEvent


def make_endpoint(endpoint_id="ep1", **overrides) -> WebhookEndpointConfig:
    fields = {
        "endpoint_id": endpoint_id,
        "name": f"Endpoint {endpoint_id}",
        "target_url": "https://example.test/hook",
        "events": frozenset({"subscription", "follow", "chat"}),
    }
    fields.update(overrides)
    return WebhookEndpointConfig(**fields)


def make_event(event_type="subscription", platform="kick", data=None, event_id="evt-1", timestamp_ms=1_731_289_200_000):
    return WebhookEvent(event_id, event_type, platform, timestamp_ms, data or {"username": "viewer123"})


def make_job(endpoint_id="ep1", event_type="subscription", **endpoint_overrides) -> DeliveryJob:
    return DeliveryJob(make_endpoint(endpoint_id, **endpoint_overrides), make_event(event_type))
