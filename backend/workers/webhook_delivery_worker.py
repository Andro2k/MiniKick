# backend\workers\webhook_delivery_worker.py

import heapq
import itertools
import logging
import queue
import random
import threading
import time
from typing import Callable

from backend.interfaces.i_webhooks import DeliveryJob, DeliveryResponse

logger = logging.getLogger("minikick.workers.webhook_delivery")

DeliverFn = Callable[[DeliveryJob], DeliveryResponse]
BackoffFn = Callable[[int], float]

MAX_DELAY_S = 30.0
_POLL_INTERVAL_S = 0.25
_EPHEMERAL_FILL_RATIO = 0.8
_LOOP_ERROR_PAUSE_S = 0.5


def full_jitter_backoff(attempt: int) -> float:
    return random.uniform(0.0, min(MAX_DELAY_S, 2.0 ** attempt))


class WebhookDeliveryWorker:
    def __init__(
        self,
        deliver: DeliverFn,
        *,
        max_pending: int = 1000,
        max_attempts: int = 4,
        backoff: BackoffFn = full_jitter_backoff,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._deliver = deliver
        self._max_attempts = max_attempts
        self._backoff = backoff
        self._clock = clock
        self._max_pending = max_pending
        self._ephemeral_limit = int(max_pending * _EPHEMERAL_FILL_RATIO)
        self._queue: queue.Queue[DeliveryJob] = queue.Queue()
        self._retry_heap: list[tuple[float, int, DeliveryJob]] = []
        self._cooldowns: dict[str, float] = {}
        self._sequence = itertools.count()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="WebhookDelivery", daemon=True)
        self._dropped = 0
        self._dropped_lock = threading.Lock()

    @property
    def dropped_count(self) -> int:
        return self._dropped

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 1.5) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout)

    def submit(self, job: DeliveryJob, critical: bool) -> bool:
        limit = self._max_pending if critical else self._ephemeral_limit
        if self._stop_event.is_set() or self._pending() >= limit:
            self._register_drop(job, critical)
            return False
        self._queue.put_nowait(job)
        return True

    def _pending(self) -> int:
        return self._queue.qsize() + len(self._retry_heap)

    def _register_drop(self, job: DeliveryJob, critical: bool) -> None:
        with self._dropped_lock:
            self._dropped += 1
            total = self._dropped
        if critical or total % 100 == 1:
            logger.warning(
                "[Webhooks] Queue saturated; dropped %s event '%s' (total dropped: %d).",
                "critical" if critical else "ephemeral", job.event.event_type, total,
            )

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                job = self._next_job()
                if job is not None:
                    self._process(job)
            except Exception:
                logger.exception("[Webhooks] Unexpected error in the delivery loop.")
                self._stop_event.wait(_LOOP_ERROR_PAUSE_S)

    def _next_job(self) -> DeliveryJob | None:
        now = self._clock()
        if self._retry_heap and self._retry_heap[0][0] <= now:
            _, _, job = heapq.heappop(self._retry_heap)
            return self._admit(job, now)
        try:
            job = self._queue.get(timeout=self._wait_time(now))
        except queue.Empty:
            return None
        return self._admit(job, self._clock())

    def _wait_time(self, now: float) -> float:
        if not self._retry_heap:
            return _POLL_INTERVAL_S
        return max(0.0, min(_POLL_INTERVAL_S, self._retry_heap[0][0] - now))

    def _admit(self, job: DeliveryJob, now: float) -> DeliveryJob | None:
        cooldown_until = self._cooldowns.get(job.endpoint.endpoint_id, 0.0)
        if cooldown_until > now:
            self._schedule(job, cooldown_until)
            return None
        return job

    def _schedule(self, job: DeliveryJob, not_before: float) -> None:
        heapq.heappush(self._retry_heap, (not_before, next(self._sequence), job))

    def _process(self, job: DeliveryJob) -> None:
        try:
            response = self._deliver(job)
        except Exception as err:
            response = DeliveryResponse(error=type(err).__name__)
        endpoint_id = job.endpoint.endpoint_id
        if response.ok:
            self._cooldowns.pop(endpoint_id, None)
            return
        label = f"'{job.endpoint.name}' ({job.event.event_type})"
        detail = response.error or f"HTTP {response.status_code}"
        if not response.retryable:
            logger.warning("[Webhooks] %s rejected: %s. Not retrying.", label, detail)
            return
        retry = job.next_attempt()
        if retry.attempt >= self._max_attempts:
            logger.warning("[Webhooks] %s dropped after %d attempts: %s.", label, retry.attempt, detail)
            return
        not_before = self._clock() + self._retry_delay(response, retry.attempt)
        self._cooldowns[endpoint_id] = not_before
        self._schedule(retry, not_before)

    def _retry_delay(self, response: DeliveryResponse, attempt: int) -> float:
        if response.retry_after is not None:
            return min(response.retry_after, MAX_DELAY_S)
        return self._backoff(attempt)
