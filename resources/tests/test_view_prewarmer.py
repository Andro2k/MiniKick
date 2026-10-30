# resources\tests\test_view_prewarmer.py

from frontend.view_prewarmer import ViewPrewarmer


class _Scheduler:
    def __init__(self):
        self.calls = []

    def __call__(self, delay_ms, callback):
        self.calls.append((delay_ms, callback))

    def run_next(self):
        _, callback = self.calls.pop(0)
        callback()

    def drain(self, limit=50):
        for _ in range(limit):
            if not self.calls:
                return
            self.run_next()
        raise AssertionError("el prewarmer no termina")


class _Harness:
    def __init__(self, names=("Chat", "Music", "Settings"), idle_for=10.0, active=True, fail_on=None):
        self.created = set()
        self.order = []
        self.idle_for = idle_for
        self.active = active
        self.fail_on = fail_on
        self.scheduler = _Scheduler()
        self.prewarmer = ViewPrewarmer(
            create_view=self._create,
            view_names=names,
            is_created=lambda name: name in self.created,
            is_active=lambda: self.active,
            seconds_since_navigation=lambda: self.idle_for,
            schedule=self.scheduler,
            step_delay_ms=150,
            busy_delay_ms=600,
            idle_threshold_s=0.6,
        )

    def _create(self, name):
        if name == self.fail_on:
            raise RuntimeError("boom")
        self.created.add(name)
        self.order.append(name)


def test_creates_views_in_order_one_per_step_with_the_configured_delays():
    h = _Harness()
    h.prewarmer.start(initial_delay_ms=1500)

    assert h.scheduler.calls[0][0] == 1500
    h.scheduler.run_next()
    assert h.order == ["Chat"] and h.scheduler.calls[0][0] == 150
    h.scheduler.drain()
    assert h.order == ["Chat", "Music", "Settings"]


def test_skips_views_the_user_already_opened():
    h = _Harness()
    h.created.add("Music")
    h.prewarmer.start()
    h.scheduler.drain()
    assert h.order == ["Chat", "Settings"]


def test_defers_while_the_user_is_navigating_and_resumes_when_idle():
    h = _Harness(idle_for=0.1)
    h.prewarmer.start()
    h.scheduler.run_next()
    assert h.order == [] and h.scheduler.calls[0][0] == 600

    h.idle_for = 5.0
    h.scheduler.drain()
    assert h.order == ["Chat", "Music", "Settings"]


def test_stops_when_the_window_is_shutting_down():
    h = _Harness()
    h.prewarmer.start()
    h.scheduler.run_next()
    h.active = False
    h.scheduler.run_next()
    assert h.order == ["Chat"] and h.scheduler.calls == []


def test_a_failing_view_does_not_stop_the_rest():
    h = _Harness(fail_on="Music")
    h.prewarmer.start()
    h.scheduler.drain()
    assert h.order == ["Chat", "Settings"]


def test_start_is_idempotent_and_finishes_without_rescheduling():
    h = _Harness(names=("Chat",))
    h.prewarmer.start()
    h.prewarmer.start()
    assert len(h.scheduler.calls) == 1
    h.scheduler.drain()
    assert h.order == ["Chat"] and h.scheduler.calls == []
