# resources\tests\test_stats_module.py
"""Pruebas del módulo de estadísticas: almacenamiento, servicio, métricas por hora y vista."""

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backend.database import DatabaseManager, SQLiteStatsStorage
from backend.services.stats import StatsService
from frontend.window.session_metrics_tracker import SessionMetrics

TODAY = date(2026, 11, 15)


class KeyTranslations:
    @staticmethod
    def get(key):
        return key


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return DatabaseManager(db_name="stats_test.db")


@pytest.fixture
def storage(db):
    return SQLiteStatsStorage(db)


def _insert_logs(db, rows):
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        for sql, params in rows:
            conn.execute(sql, params)
        conn.commit()


def test_hourly_counts_accumulate_and_split_by_platform(storage):
    storage.add_hourly_counts({("2026-11-15", 10, "kick"): 3, ("2026-11-15", 10, "twitch"): 2})
    storage.add_hourly_counts({("2026-11-15", 10, "kick"): 4})

    hourly = storage.get_hourly_messages("2026-11-15", "2026-11-15")
    assert hourly["2026-11-15"][10] == 9
    assert storage.get_platform_messages("2026-11-15", "2026-11-15") == {"kick": 7, "twitch": 2}


def test_prune_old_removes_only_expired_days(storage):
    old = (date.today() - timedelta(days=200)).strftime("%Y-%m-%d")
    storage.add_hourly_counts({(old, 1, "kick"): 5, (date.today().strftime("%Y-%m-%d"), 1, "kick"): 5})
    storage.prune_old(keep_days=90)
    assert storage.get_hourly_messages(old, old) == {}
    assert len(storage.get_hourly_messages("2000-01-01", "2100-01-01")) == 1


def test_today_snapshot_compares_with_yesterday_and_finds_peak(storage):
    storage.add_hourly_counts({
        ("2026-11-15", 9, "kick"): 10, ("2026-11-15", 20, "kick"): 30,
        ("2026-11-14", 9, "kick"): 20,
    })
    snapshot = StatsService(storage).build_snapshot("today", today=TODAY)

    assert snapshot.is_hourly and len(snapshot.labels) == 24
    assert snapshot.kpis["messages"] == (40, 20)
    assert snapshot.current_series[20] == 30 and snapshot.previous_series[9] == 20
    assert snapshot.peak_hour == 20
    assert snapshot.peak_share == pytest.approx(75.0)


def test_seven_day_snapshot_aggregates_per_day(storage):
    storage.add_hourly_counts({
        ("2026-11-15", 1, "kick"): 5, ("2026-11-09", 1, "kick"): 7,
        ("2026-11-08", 1, "kick"): 10,
    })
    snapshot = StatsService(storage).build_snapshot("7d", today=TODAY)

    assert not snapshot.is_hourly and len(snapshot.labels) == 7
    assert snapshot.current_series[0] == 7 and snapshot.current_series[-1] == 5
    assert snapshot.kpis["messages"] == (12, 10)


def test_activity_totals_and_top_commands_use_local_timestamps(db, storage):
    _insert_logs(db, [
        ("INSERT INTO command_execution_logs (command_trigger, username, platform, timestamp) VALUES (?,?,?,?)", p)
        for p in (("!hi", "a", "kick", "2026-11-15 10:00:00"), ("!hi", "b", "kick", "2026-11-15 23:59:59"),
                  ("!lurk", "c", "kick", "2026-11-15 11:00:00"), ("!hi", "d", "kick", "2026-11-14 12:00:00"))
    ] + [
        ("INSERT INTO spam_violations (username, sender_id, filter_id, penalty_type, platform, timestamp) VALUES (?,?,?,?,?,?)",
         ("x", "1", "caps", "timeout", "kick", "2026-11-15 09:00:00")),
    ])

    assert storage.get_activity_totals("2026-11-15", "2026-11-15") == {"commands": 3, "redemptions": 0, "spam": 1}
    assert storage.get_top_commands("2026-11-15", "2026-11-15") == [
        {"trigger": "!hi", "count": 2}, {"trigger": "!lurk", "count": 1}]


def test_empty_database_produces_a_safe_snapshot(storage):
    snapshot = StatsService(storage).build_snapshot("30d", today=TODAY)
    assert snapshot.peak_hour is None and snapshot.peak_share == 0.0
    assert snapshot.kpis["messages"] == (0, 0) and len(snapshot.labels) == 30


def test_session_metrics_buffers_messages_per_hour_and_flushes(qapp):
    sink_calls = []
    clock = iter([datetime(2026, 11, 15, 10, 5), datetime(2026, 11, 15, 10, 50), datetime(2026, 11, 15, 11, 0)])
    metrics = SessionMetrics(lambda: {}, hourly_sink=sink_calls.append, clock=lambda: next(clock))
    metrics.record_message("kick")
    metrics.record_message("kick")
    metrics.record_message("twitch")

    metrics.flush_hourly_counts(sync=True)
    metrics.flush_hourly_counts(sync=True)

    assert sink_calls == [{("2026-11-15", 10, "kick"): 2, ("2026-11-15", 11, "twitch"): 1}]
    metrics.stop()


def test_session_metrics_keeps_pending_counts_when_the_write_fails(qapp):
    attempts = []

    def flaky_sink(batch):
        attempts.append(dict(batch))
        if len(attempts) == 1:
            raise RuntimeError("db locked")

    metrics = SessionMetrics(lambda: {}, hourly_sink=flaky_sink, clock=lambda: datetime(2026, 11, 15, 8, 0))
    metrics.record_message("kick")
    metrics.flush_hourly_counts(sync=True)
    metrics.flush_hourly_counts(sync=True)

    assert attempts[1] == {("2026-11-15", 8, "kick"): 1}
    metrics.stop()


def test_stats_view_renders_a_snapshot_and_dashboard_no_longer_has_stats(qapp, storage):
    from frontend.views.dashboard_view import DashboardView
    from frontend.views.stats_view import StatsView

    storage.add_hourly_counts({("2026-11-15", 9, "kick"): 12, ("2026-11-15", 9, "twitch"): 4})
    view = StatsView(KeyTranslations())
    view.render_snapshot(StatsService(storage).build_snapshot("today", today=TODAY))

    assert view.kpi_cards["messages"].lbl_value.text() == "16"
    assert view.platform_bars["kick"][0].value() == 75
    assert view.combo_period.count() == 3

    dashboard = DashboardView(KeyTranslations())
    assert not any(hasattr(dashboard, name) for name in ("session_grid", "chatters_table", "top_commands_card"))


def test_stats_controller_changes_period_and_loads_chatters(qapp, storage):
    from backend.controllers import StatsController
    from frontend.views.stats_view import StatsView

    view = StatsView(KeyTranslations())
    widget_service = SimpleNamespace(
        get_available_chatter_dates=lambda: [],
        load_daily_chatters=lambda _d: {"a": {"user": "a", "count": 5}},
        get_widget=lambda _id: {"is_active": True},
    )
    flushes = []
    controller = StatsController(view, StatsService(storage), widget_service=widget_service,
                                 flush_pending=lambda: flushes.append(1))
    view.combo_period.setCurrentIndex(1)

    assert controller._period == "7d" and len(flushes) >= 2
    assert view.chatters_table.table.rowCount() == 1
