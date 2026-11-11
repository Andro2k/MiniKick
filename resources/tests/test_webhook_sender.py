# resources\tests\test_webhook_sender.py

import hashlib
import hmac

from backend.interfaces.i_webhooks import DeliveryResponse
from backend.services.webhooks.webhook_formatters import GenericJsonFormatter
from backend.services.webhooks.webhook_sender import WebhookSender
from backend.services.webhooks.webhook_signer import (
    EVENT_ID_HEADER, SIGNATURE_HEADER, TIMESTAMP_HEADER, build_headers, sign_payload,
)
from resources.tests._webhook_helpers import make_job


class RecordingTransport:
    def __init__(self):
        self.calls = []

    def post(self, url, headers, body):
        self.calls.append((url, dict(headers), body))
        return DeliveryResponse(status_code=204)


def test_signature_matches_timestamp_dot_body_hmac():
    expected = hmac.new(b"s3cret", b"1700.{}", hashlib.sha256).hexdigest()
    assert sign_payload(b"{}", "s3cret", 1700) == expected


def test_headers_only_sign_when_a_secret_is_configured():
    unsigned = build_headers("evt", b"{}", "", 5)
    signed = build_headers("evt", b"{}", "k", 5)
    assert SIGNATURE_HEADER not in unsigned
    assert signed[SIGNATURE_HEADER] == sign_payload(b"{}", "k", 5)
    assert signed[EVENT_ID_HEADER] == "evt" and signed[TIMESTAMP_HEADER] == "5"


def test_retry_keeps_event_id_but_signs_with_a_fresh_timestamp():
    transport = RecordingTransport()
    clock = iter([1000, 2000])
    sender = WebhookSender({"generic": GenericJsonFormatter()}, transport, clock_ms=lambda: next(clock))
    job = make_job(hmac_secret="k")
    sender.send(job)
    sender.send(job.next_attempt())
    first, second = transport.calls[0][1], transport.calls[1][1]
    assert first[EVENT_ID_HEADER] == second[EVENT_ID_HEADER]
    assert first[TIMESTAMP_HEADER] != second[TIMESTAMP_HEADER]
    assert first[SIGNATURE_HEADER] != second[SIGNATURE_HEADER]


def test_unknown_formatter_is_a_permanent_failure_without_network_call():
    transport = RecordingTransport()
    response = WebhookSender({}, transport).send(make_job(formatter="nope"))
    assert response.permanent and not response.retryable
    assert transport.calls == []
