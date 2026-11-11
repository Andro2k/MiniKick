# resources\tests\test_webhook_transport.py

import httpx

from backend.services.webhooks.webhook_transport import HttpWebhookTransport, validate_target_url

DISCORD_URL = "https://discord.com/api/webhooks/123456/SECRET-token_abc"


def _transport(handler) -> HttpWebhookTransport:
    return HttpWebhookTransport(httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False))


def test_success_and_status_classification():
    ok = _transport(lambda request: httpx.Response(204)).post("https://example.test/h", {}, b"{}")
    bad = _transport(lambda request: httpx.Response(400)).post("https://example.test/h", {}, b"{}")
    down = _transport(lambda request: httpx.Response(503)).post("https://example.test/h", {}, b"{}")
    assert ok.ok
    assert not bad.ok and not bad.retryable
    assert down.retryable


def test_rate_limit_exposes_retry_after():
    response = _transport(lambda request: httpx.Response(429, headers={"Retry-After": "2.5"})).post(DISCORD_URL, {}, b"{}")
    assert response.retryable and response.retry_after == 2.5


def test_redirects_are_not_followed():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(302, headers={"Location": "https://evil.test/steal"})

    response = _transport(handler).post("https://example.test/h", {}, b"{}")
    assert seen == ["https://example.test/h"]
    assert response.status_code == 302 and not response.retryable


def test_timeout_is_retryable():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    response = _transport(handler).post("https://example.test/h", {}, b"{}")
    assert response.error == "timeout" and response.retryable


def test_network_errors_never_leak_the_webhook_token():
    def handler(request):
        raise httpx.ConnectError(f"cannot reach {request.url}", request=request)

    response = _transport(handler).post(DISCORD_URL, {}, b"{}")
    assert "SECRET-token_abc" not in response.error


def test_url_validation_rules():
    assert validate_target_url("http://192.168.1.50:8123/api/webhook/abc") is None
    assert validate_target_url(DISCORD_URL) is None
    assert validate_target_url(DISCORD_URL.replace("https", "http")) == "discord_requires_https"
    assert validate_target_url("http://canary.discord.com/api/webhooks/1/x") == "discord_requires_https"
    assert validate_target_url("ftp://example.test/x") == "invalid_url"
    assert validate_target_url("not a url") == "invalid_url"


def test_invalid_url_is_permanent_and_makes_no_request():
    calls = []
    transport = _transport(lambda request: calls.append(request) or httpx.Response(204))
    response = transport.post("http://discord.com/api/webhooks/1/x", {}, b"{}")
    assert response.permanent and calls == []
