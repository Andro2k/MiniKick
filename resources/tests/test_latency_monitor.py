# resources\tests\test_latency_monitor.py

import logging
from backend.utils import LatencyMonitor


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_slow_sample_warns_once_per_cooldown(caplog):
    clock = FakeClock()
    mon = LatencyMonitor("test", warn_threshold_s=1.0, warn_cooldown_s=30.0, report_interval_s=999, clock=clock)
    with caplog.at_level(logging.WARNING, logger="minikick.utils.latency"):
        mon.record(0.2)
        mon.record(3.0)
        mon.record(4.0)
        assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 1
        clock.now += 31
        mon.record(5.0)
        assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 2


def test_fast_samples_never_warn(caplog):
    mon = LatencyMonitor("test", warn_threshold_s=1.0, report_interval_s=999, clock=FakeClock())
    with caplog.at_level(logging.WARNING, logger="minikick.utils.latency"):
        for _ in range(50):
            mon.record(0.05)
    assert not caplog.records


def test_p95_and_periodic_report(caplog):
    clock = FakeClock()
    mon = LatencyMonitor("net", warn_threshold_s=999, report_interval_s=60.0, clock=clock)
    with caplog.at_level(logging.INFO, logger="minikick.utils.latency"):
        for i in range(100):
            mon.record(i / 100)
        assert 0.9 <= mon.p95 <= 0.99
        assert not caplog.records
        clock.now += 61
        mon.record(0.5)
    reports = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert len(reports) == 1
    assert "[Latency/net]" in reports[0] and "n=101" in reports[0]


def test_report_is_skipped_when_no_samples(caplog):
    clock = FakeClock()
    mon = LatencyMonitor("idle", report_interval_s=10.0, clock=clock)
    with caplog.at_level(logging.INFO, logger="minikick.utils.latency"):
        clock.now += 100
        mon._report(clock.now)
    assert not caplog.records


def test_periodic_report_maximum_handles_all_negative_samples(caplog):
    clock = FakeClock()
    mon = LatencyMonitor("clock-skew", report_interval_s=10.0, clock=clock)
    with caplog.at_level(logging.INFO, logger="minikick.utils.latency"):
        mon.record(-2.0)
        mon.record(-1.0)
        clock.now += 11
        mon.record(-3.0)

    report = next(record.getMessage() for record in caplog.records if record.levelno == logging.INFO)
    assert "max=-1.000s" in report
