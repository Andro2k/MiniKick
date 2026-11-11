# resources\tests\test_webhook_dispatcher.py

from backend.services.webhooks.webhook_dispatcher_service import WebhookDispatcherService
from resources.tests._webhook_helpers import make_endpoint


def _dispatcher(endpoints):
    submitted = []
    service = WebhookDispatcherService(
        lambda: endpoints,
        lambda job, critical: submitted.append((job, critical)) or True,
        clock_ms=lambda: 42,
    )
    return service, submitted


def test_routes_only_to_matching_endpoints():
    endpoints = [
        make_endpoint("a"),
        make_endpoint("b", events=frozenset({"raid"})),
        make_endpoint("c", platforms=frozenset({"twitch"})),
        make_endpoint("d", enabled=False),
    ]
    service, submitted = _dispatcher(endpoints)
    service.post_event("subscription", "kick", {"username": "viewer123"})
    assert [job.endpoint.endpoint_id for job, _ in submitted] == ["a"]


def test_one_event_id_is_shared_across_destinations():
    service, submitted = _dispatcher([make_endpoint("a"), make_endpoint("b")])
    service.post_event("follow", "twitch", {})
    ids = {job.event.event_id for job, _ in submitted}
    assert len(submitted) == 2 and len(ids) == 1
    assert submitted[0][0].event.timestamp_ms == 42


def test_event_priority_lane_follows_event_type():
    service, submitted = _dispatcher([make_endpoint("a")])
    service.post_event("subscription", "kick", {})
    service.post_event("chat", "kick", {})
    assert [critical for _, critical in submitted] == [True, False]


def test_no_work_when_nothing_matches():
    service, submitted = _dispatcher([make_endpoint("a")])
    service.post_event("raid", "kick", {})
    assert submitted == []
