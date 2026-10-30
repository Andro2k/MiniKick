# resources\tests\test_log_writer.py

import threading
import time

from backend.services.system.log_writer import BatchedLogWriter


class _Sink:
    def __init__(self, delay=0.0, fail_first=False):
        self.batches = []
        self.delay = delay
        self.fail_first = fail_first
        self.threads = set()

    def __call__(self, records):
        self.threads.add(threading.current_thread().name)
        if self.delay:
            time.sleep(self.delay)
        if self.fail_first:
            self.fail_first = False
            raise RuntimeError("disco lleno")
        self.batches.append(list(records))

    @property
    def flat(self):
        return [r for batch in self.batches for r in batch]


def test_records_are_batched_and_keep_their_order():
    sink = _Sink()
    writer = BatchedLogWriter(sink, flush_interval_s=0.05)
    for n in range(50):
        writer.submit(("INF", "t", f"m{n}"))

    assert writer.flush()
    assert sink.flat == [("INF", "t", f"m{n}") for n in range(50)]
    assert len(sink.batches) < 10
    writer.close()


def test_submit_does_not_block_on_a_slow_storage():
    sink = _Sink(delay=0.3)
    writer = BatchedLogWriter(sink, flush_interval_s=0.01)

    started = time.perf_counter()
    for n in range(30):
        writer.submit(("INF", "t", f"m{n}"))
    elapsed = time.perf_counter() - started

    assert elapsed < 0.1
    assert writer.flush(timeout=5)
    assert len(sink.flat) == 30
    writer.close()


def test_writes_happen_off_the_calling_thread():
    sink = _Sink()
    writer = BatchedLogWriter(sink, flush_interval_s=0.01)
    writer.submit(("INF", "t", "x"))
    writer.flush()
    assert sink.threads == {"LogBatchWriter"}
    writer.close()


def test_flush_reports_timeout_when_storage_is_too_slow():
    sink = _Sink(delay=0.5)
    writer = BatchedLogWriter(sink, flush_interval_s=0.01)
    writer.submit(("INF", "t", "x"))
    assert writer.flush(timeout=0.05) is False
    assert writer.flush(timeout=5) is True
    writer.close()


def test_close_drains_pending_records_and_ignores_later_submits():
    sink = _Sink()
    writer = BatchedLogWriter(sink, flush_interval_s=5.0)
    for n in range(5):
        writer.submit(("INF", "t", f"m{n}"))

    writer.close()
    writer.submit(("INF", "t", "late"))

    assert [r[2] for r in sink.flat] == ["m0", "m1", "m2", "m3", "m4"]


def test_storage_failure_loses_that_batch_but_keeps_the_writer_alive():
    sink = _Sink(fail_first=True)
    writer = BatchedLogWriter(sink, flush_interval_s=0.01)
    writer.submit(("INF", "t", "lost"))
    writer.flush()
    writer.submit(("INF", "t", "kept"))
    writer.flush()

    assert [r[2] for r in sink.flat] == ["kept"]
    writer.close()


def test_close_without_any_record_does_not_start_a_thread():
    writer = BatchedLogWriter(_Sink())
    writer.close()
    assert writer._thread is None
