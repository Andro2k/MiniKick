# resources\tests\test_webhook_management_service.py

import pytest

from backend.config.toml_config_provider import TomlConfigProvider
from backend.config.webhook_endpoint_store import WebhookEndpointStore
from backend.interfaces.i_webhooks import DeliveryResponse
from backend.services.webhooks import WebhookManagementService
from resources.tests.test_webhook_endpoint_store import ReversibleCipher

URL = "https://discord.com/api/webhooks/123456/SECRET-token_abc"


class FakeSender:
    def __init__(self, response=None, error=None):
        self.response = response or DeliveryResponse(status_code=204)
        self.error = error
        self.jobs = []

    def send(self, job):
        self.jobs.append(job)
        if self.error:
            raise self.error
        return self.response


def _service(tmp_path, sender=None):
    store = WebhookEndpointStore(TomlConfigProvider(tmp_path / "config.toml"), ReversibleCipher())
    return WebhookManagementService(store, (sender or FakeSender()).send, clock_ms=lambda: 1000)


def _data(**overrides):
    data = {"name": "Alerts", "formatter": "discord", "target_url": URL, "events": ["follow", "raid"], "platforms": ["kick"]}
    data.update(overrides)
    return data


def test_save_creates_then_updates_the_same_endpoint(tmp_path):
    service = _service(tmp_path)
    created = service.save_endpoint(_data())
    service.save_endpoint(_data(endpoint_id=created.endpoint_id, name="Renamed"))
    endpoints = service.list_endpoints()
    assert [ep.name for ep in endpoints] == ["Renamed"]
    assert endpoints[0].events == frozenset({"follow", "raid"})


def test_save_drops_unknown_events_and_platforms(tmp_path):
    saved = _service(tmp_path).save_endpoint(_data(events=["follow", "bogus"], platforms=["kick", "bogus"]))
    assert saved.events == frozenset({"follow"})
    assert saved.platforms == frozenset({"kick"})


def test_discord_preset_never_keeps_a_secret(tmp_path):
    saved = _service(tmp_path).save_endpoint(_data(hmac_secret="abc"))
    assert saved.hmac_secret == ""
    assert _service(tmp_path).save_endpoint(_data(formatter="generic", hmac_secret="abc")).hmac_secret == "abc"


@pytest.mark.parametrize("overrides", [{"name": " "}, {"target_url": ""}, {"target_url": "ftp://x.test"}, {"formatter": "other"}])
def test_save_rejects_invalid_data(tmp_path, overrides):
    with pytest.raises(ValueError):
        _service(tmp_path).save_endpoint(_data(**overrides))


def test_delete_and_toggle(tmp_path):
    service = _service(tmp_path)
    ep = service.save_endpoint(_data())
    assert service.set_enabled(ep.endpoint_id, False) is True
    assert service.set_enabled(ep.endpoint_id, False) is False
    assert service.get_endpoint(ep.endpoint_id).enabled is False
    assert service.delete_endpoint(ep.endpoint_id) is True
    assert service.delete_endpoint(ep.endpoint_id) is False
    assert service.list_endpoints() == []


def test_validate_url_reports_codes():
    assert WebhookManagementService.validate_url("https://example.test/h") is None
    assert WebhookManagementService.validate_url("nope") == "invalid_url"
    assert WebhookManagementService.validate_url("http://discord.com/api/webhooks/1/x") == "discord_requires_https"


def test_test_ping_sends_a_test_event_without_saving(tmp_path):
    sender = FakeSender()
    service = _service(tmp_path, sender)
    result = service.send_test_ping(_data())
    assert result.ok and result.status_code == 204
    assert sender.jobs[0].event.event_type == "test"
    assert service.list_endpoints() == []


def test_test_ping_reports_failures(tmp_path):
    failed = _service(tmp_path, FakeSender(DeliveryResponse(status_code=404))).send_test_ping(_data())
    assert (failed.ok, failed.error) == (False, "HTTP 404")
    crashed = _service(tmp_path, FakeSender(error=RuntimeError("boom"))).send_test_ping(_data())
    assert (crashed.ok, crashed.error) == (False, "RuntimeError")
    assert _service(tmp_path).send_test_ping(_data(name="")).error == "invalid_data"


def test_summaries_expose_no_url_or_secret(tmp_path):
    service = _service(tmp_path)
    service.save_endpoint(_data(formatter="generic", hmac_secret="topsecret"))
    summary = service.list_summaries()[0]
    assert summary.name == "Alerts" and summary.events == frozenset({"follow", "raid"})
    assert "SECRET" not in repr(summary) and "topsecret" not in repr(summary)


def test_save_requires_at_least_one_event_and_one_platform(tmp_path):
    service = _service(tmp_path)
    for overrides in ({"events": []}, {"platforms": []}):
        with pytest.raises(ValueError):
            service.save_endpoint(_data(**overrides))
    assert service.list_endpoints() == []
