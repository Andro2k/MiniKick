# resources\tests\test_webhook_worker.py

import threading
import time

from backend.interfaces.i_webhooks import DeliveryResponse
from backend.workers.webhook_delivery_worker import WebhookDeliveryWorker
from resources.tests._webhook_helpers import make_job

WAIT_S = 3.0


def _worker(deliver, **kwargs) -> WebhookDeliveryWorker:
    kwargs.setdefault("backoff", lambda attempt: 0.01)
    return WebhookDeliveryWorker(deliver, **kwargs)


def test_delivers_submitted_jobs():
    done = threading.Event()
    worker = _worker(lambda job: (done.set(), DeliveryResponse(status_code=204))[1])
    worker.start()
    try:
        assert worker.submit(make_job(), critical=True)
        assert done.wait(WAIT_S)
    finally:
        worker.stop()


def test_retries_transient_failures_then_succeeds():
    statuses = iter([503, 500, 204])
    calls = []
    done = threading.Event()

    def deliver(job):
        status = next(statuses)
        calls.append(job.attempt)
        if status == 204:
            done.set()
        return DeliveryResponse(status_code=status)

    worker = _worker(deliver)
    worker.start()
    try:
        worker.submit(make_job(), critical=True)
        assert done.wait(WAIT_S)
    finally:
        worker.stop()
    assert calls == [0, 1, 2]


def test_gives_up_after_max_attempts():
    calls = []
    fourth = threading.Event()

    def deliver(job):
        calls.append(job.attempt)
        if len(calls) == 4:
            fourth.set()
        return DeliveryResponse(status_code=500)

    worker = _worker(deliver, max_attempts=4)
    worker.start()
    try:
        worker.submit(make_job(), critical=True)
        assert fourth.wait(WAIT_S)
        time.sleep(0.2)
    finally:
        worker.stop()
    assert len(calls) == 4


def test_client_errors_are_not_retried():
    calls = []
    worker = _worker(lambda job: calls.append(job) or DeliveryResponse(status_code=400))
    worker.start()
    try:
        worker.submit(make_job(), critical=True)
        time.sleep(0.3)
    finally:
        worker.stop()
    assert len(calls) == 1


def test_rate_limited_endpoint_does_not_block_healthy_ones():
    delivered = []
    healthy_done = threading.Event()

    def deliver(job):
        if job.endpoint.endpoint_id == "limited":
            return DeliveryResponse(status_code=429, retry_after=2.0)
        delivered.append(job.endpoint.endpoint_id)
        healthy_done.set()
        return DeliveryResponse(status_code=204)

    worker = _worker(deliver)
    worker.start()
    try:
        worker.submit(make_job("limited"), critical=True)
        worker.submit(make_job("healthy"), critical=True)
        assert healthy_done.wait(1.0)
    finally:
        worker.stop()
    assert delivered == ["healthy"]


def test_jobs_for_a_cooling_endpoint_wait_for_the_cooldown():
    calls = []
    worker = _worker(lambda job: calls.append(job.endpoint.endpoint_id) or DeliveryResponse(status_code=429, retry_after=1.5))
    worker.start()
    try:
        worker.submit(make_job("limited"), critical=True)
        time.sleep(0.2)
        worker.submit(make_job("limited", event_type="follow"), critical=True)
        time.sleep(0.3)
    finally:
        worker.stop()
    assert len(calls) == 1


def test_ephemeral_events_are_dropped_at_80_percent_but_critical_still_fit():
    worker = _worker(lambda job: DeliveryResponse(status_code=204), max_pending=10)
    results = [worker.submit(make_job(event_type="chat"), critical=False) for _ in range(9)]
    assert results == [True] * 8 + [False]
    assert worker.dropped_count == 1
    assert worker.submit(make_job(), critical=True)
    assert worker.submit(make_job(), critical=True)
    assert not worker.submit(make_job(), critical=True)
    assert worker.dropped_count == 2


def test_stop_returns_within_deadline_even_with_a_hung_request():
    started, release = threading.Event(), threading.Event()

    def deliver(job):
        started.set()
        release.wait(5.0)
        return DeliveryResponse(status_code=204)

    worker = _worker(deliver)
    worker.start()
    worker.submit(make_job(), critical=True)
    assert started.wait(WAIT_S)
    began = time.monotonic()
    try:
        worker.stop(timeout=0.2)
        assert time.monotonic() - began < 1.0
    finally:
        release.set()


def test_submit_after_stop_is_rejected():
    worker = _worker(lambda job: DeliveryResponse(status_code=204))
    worker.stop()
    assert not worker.submit(make_job(), critical=True)
