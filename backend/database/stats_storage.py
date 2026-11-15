# backend\database\stats_storage.py
"""Almacenamiento SQLite de las estadísticas del canal (mensajes por hora y actividad)."""

import logging
from datetime import date, timedelta
from .database_manager import DatabaseManager

logger = logging.getLogger("minikick.database.stats")

HourlyKey = tuple[str, int, str]


class SQLiteStatsStorage:
    RETENTION_DAYS = 90

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_hourly_counts(self, counts: dict[HourlyKey, int]) -> None:
        """Suma al acumulado los mensajes pendientes, claves (fecha, hora, plataforma)."""
        if not counts:
            return
        rows = [(d, h, p, n) for (d, h, p), n in counts.items() if n > 0]
        try:
            with self.db_manager.get_connection() as conn:
                conn.executemany(
                    """
                    INSERT INTO hourly_message_stats (stat_date, hour, platform, message_count)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(stat_date, hour, platform)
                    DO UPDATE SET message_count = message_count + excluded.message_count
                    """,
                    rows,
                )
                conn.commit()
        except Exception as e:
            logger.error("[StatsStorage] Error saving hourly counts: %s", e)
            raise

    def prune_old(self, keep_days: int = RETENTION_DAYS) -> None:
        cutoff = (date.today() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM hourly_message_stats WHERE stat_date < ?", (cutoff,))
                conn.commit()
        except Exception as e:
            logger.error("[StatsStorage] Error pruning hourly stats: %s", e)

    def get_hourly_messages(self, start: str, end: str) -> dict[str, list[int]]:
        """Mensajes por día y hora en el rango: {fecha: [24 valores]}."""
        result: dict[str, list[int]] = {}
        try:
            with self.db_manager.get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT stat_date, hour, SUM(message_count)
                    FROM hourly_message_stats
                    WHERE stat_date BETWEEN ? AND ?
                    GROUP BY stat_date, hour
                    """,
                    (start, end),
                ).fetchall()
            for stat_date, hour, total in rows:
                if 0 <= hour < 24:
                    result.setdefault(stat_date, [0] * 24)[hour] = int(total)
        except Exception as e:
            logger.error("[StatsStorage] Error reading hourly messages: %s", e)
        return result

    def get_platform_messages(self, start: str, end: str) -> dict[str, int]:
        try:
            with self.db_manager.get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT platform, SUM(message_count)
                    FROM hourly_message_stats
                    WHERE stat_date BETWEEN ? AND ?
                    GROUP BY platform
                    """,
                    (start, end),
                ).fetchall()
            return {platform: int(total) for platform, total in rows}
        except Exception as e:
            logger.error("[StatsStorage] Error reading platform messages: %s", e)
            return {}

    def get_activity_totals(self, start: str, end: str) -> dict[str, int]:
        """Comandos usados, canjes y spam bloqueado en el rango (marcas de tiempo locales)."""
        lower, upper = f"{start} 00:00:00", f"{end} 23:59:59"
        totals = {"commands": 0, "redemptions": 0, "spam": 0}
        queries = {
            "commands": "SELECT COUNT(*) FROM command_execution_logs WHERE timestamp BETWEEN ? AND ?",
            "redemptions": "SELECT COUNT(*) FROM reward_redemptions WHERE timestamp BETWEEN ? AND ?",
            "spam": "SELECT COUNT(*) FROM spam_violations WHERE timestamp BETWEEN ? AND ?",
        }
        try:
            with self.db_manager.get_connection() as conn:
                for key, sql in queries.items():
                    totals[key] = int(conn.execute(sql, (lower, upper)).fetchone()[0])
        except Exception as e:
            logger.error("[StatsStorage] Error reading activity totals: %s", e)
        return totals

    def get_top_commands(self, start: str, end: str, limit: int = 5) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT command_trigger, COUNT(id) AS cnt
                    FROM command_execution_logs
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY command_trigger
                    ORDER BY cnt DESC
                    LIMIT ?
                    """,
                    (f"{start} 00:00:00", f"{end} 23:59:59", limit),
                ).fetchall()
            return [{"trigger": trigger, "count": int(count)} for trigger, count in rows]
        except Exception as e:
            logger.error("[StatsStorage] Error reading top commands: %s", e)
            return []

    def get_module_counts(self) -> dict[str, int]:
        """Comandos activos, timers activos y recompensas vinculadas."""
        counts = {"active_commands": 0, "active_timers": 0, "total_rewards": 0}
        queries = {
            "active_commands": "SELECT COUNT(*) FROM chat_commands WHERE is_active = 1",
            "active_timers": "SELECT COUNT(*) FROM chat_timers WHERE is_active = 1",
            "total_rewards": "SELECT COUNT(*) FROM obs_rewards",
        }
        try:
            with self.db_manager.get_connection() as conn:
                for key, sql in queries.items():
                    counts[key] = int(conn.execute(sql).fetchone()[0])
        except Exception as e:
            logger.error("[StatsStorage] Error reading module counts: %s", e)
        return counts
