# backend\services\stats\stats_service.py
"""Cálculo de las estadísticas del canal para un período y su comparación con el anterior."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

from backend.database import SQLiteStatsStorage

StatsPeriod = Literal["today", "7d", "30d"]
_PERIOD_DAYS: dict[str, int] = {"today": 1, "7d": 7, "30d": 30}
_FMT = "%Y-%m-%d"


@dataclass(slots=True)
class StatsSnapshot:
    """Resultado listo para pintar: totales, comparación con el período anterior y series."""

    period: str
    start: str
    end: str
    kpis: dict[str, tuple[int, int]]
    labels: list[str]
    current_series: list[int]
    previous_series: list[int]
    hourly_totals: list[int]
    peak_hour: int | None
    peak_share: float
    platform_messages: dict[str, int]
    top_commands: list[dict]
    modules: dict[str, int] = field(default_factory=dict)

    @property
    def is_hourly(self) -> bool:
        return self.period == "today"


class StatsService:
    def __init__(self, storage: SQLiteStatsStorage):
        self.storage = storage

    @staticmethod
    def period_days(period: str) -> int:
        return _PERIOD_DAYS.get(period, 1)

    def build_snapshot(self, period: str = "today", today: date | None = None) -> StatsSnapshot:
        days = self.period_days(period)
        today = today or date.today()
        start = today - timedelta(days=days - 1)
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        s, e, ps, pe = (d.strftime(_FMT) for d in (start, today, prev_start, prev_end))

        hourly = self.storage.get_hourly_messages(ps, e)
        current_days = [(start + timedelta(days=i)).strftime(_FMT) for i in range(days)]
        previous_days = [(prev_start + timedelta(days=i)).strftime(_FMT) for i in range(days)]
        empty = [0] * 24

        if days == 1:
            labels = [f"{h:02d}:00" for h in range(24)]
            current_series = list(hourly.get(current_days[0], empty))
            previous_series = list(hourly.get(previous_days[0], empty))
        else:
            labels = [d[5:] for d in current_days]
            current_series = [sum(hourly.get(d, empty)) for d in current_days]
            previous_series = [sum(hourly.get(d, empty)) for d in previous_days]

        hourly_totals = [0] * 24
        for d in current_days:
            for hour, count in enumerate(hourly.get(d, empty)):
                hourly_totals[hour] += count
        total_messages = sum(hourly_totals)
        peak_hour = max(range(24), key=hourly_totals.__getitem__) if total_messages else None
        peak_share = (hourly_totals[peak_hour] / total_messages * 100) if peak_hour is not None else 0.0

        current_activity = self.storage.get_activity_totals(s, e)
        previous_activity = self.storage.get_activity_totals(ps, pe)
        kpis = {"messages": (total_messages, sum(previous_series))}
        for key in ("commands", "redemptions", "spam"):
            kpis[key] = (current_activity[key], previous_activity[key])

        return StatsSnapshot(
            period=period,
            start=s,
            end=e,
            kpis=kpis,
            labels=labels,
            current_series=current_series,
            previous_series=previous_series,
            hourly_totals=hourly_totals,
            peak_hour=peak_hour,
            peak_share=peak_share,
            platform_messages=self.storage.get_platform_messages(s, e),
            top_commands=self.storage.get_top_commands(s, e),
            modules=self.storage.get_module_counts(),
        )
