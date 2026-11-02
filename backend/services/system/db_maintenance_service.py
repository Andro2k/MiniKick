# backend\services\system\db_maintenance_service.py

import logging
import os
import tempfile
from dataclasses import dataclass, field

from backend.database import DatabaseManager

logger = logging.getLogger("minikick.services.db_maintenance")

_VACUUM_MIN_FREE_RATIO = 0.2
_VACUUM_MIN_FREE_BYTES = 4 * 1024 * 1024
_TOP_TABLES_IN_REPORT = 5


@dataclass(frozen=True)
class DatabaseStats:
    file_bytes: int
    wal_bytes: int
    free_bytes: int
    table_rows: dict[str, int] = field(default_factory=dict)

    @property
    def free_ratio(self) -> float:
        return self.free_bytes / self.file_bytes if self.file_bytes else 0.0


class DatabaseMaintenance:
    def __init__(
        self,
        db_manager: DatabaseManager,
        vacuum_min_free_bytes: int = _VACUUM_MIN_FREE_BYTES,
        vacuum_min_free_ratio: float = _VACUUM_MIN_FREE_RATIO,
    ) -> None:
        self.db_manager = db_manager
        self._vacuum_min_free_bytes = vacuum_min_free_bytes
        self._vacuum_min_free_ratio = vacuum_min_free_ratio

    def run(self) -> DatabaseStats | None:
        try:
            before = self.collect_stats()
            self._checkpoint()
            if self._needs_vacuum(before):
                self._vacuum()
            self._optimize()
            after = self.collect_stats()
            self._log_report(before, after, self.find_obsolete_objects())
            return after
        except Exception:
            logger.exception("[Maintenance] Database maintenance failed.")
            return None

    def collect_stats(self) -> DatabaseStats:
        with self.db_manager.get_connection() as conn:
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]
            page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            free_pages = conn.execute("PRAGMA freelist_count").fetchone()[0]
            names = [
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ) if "_fts_" not in row[0]
            ]
            table_rows = {name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}
        return DatabaseStats(
            file_bytes=page_size * page_count,
            wal_bytes=self._wal_bytes(),
            free_bytes=page_size * free_pages,
            table_rows=table_rows,
        )

    def find_obsolete_objects(self) -> list[str]:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            reference = DatabaseManager(os.path.join(temp_dir, "reference.db"))
            try:
                expected = self._schema_objects(reference)
            finally:
                reference.cleanup()
        return sorted(f"{kind}:{name}" for kind, name in self._schema_objects(self.db_manager) - expected)

    @staticmethod
    def _schema_objects(db_manager: DatabaseManager) -> set[tuple[str, str]]:
        with db_manager.get_connection() as conn:
            return {
                (row[0], row[1]) for row in conn.execute(
                    "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                )
            }

    def _needs_vacuum(self, stats: DatabaseStats) -> bool:
        return stats.free_bytes >= self._vacuum_min_free_bytes and stats.free_ratio >= self._vacuum_min_free_ratio

    def _checkpoint(self) -> None:
        with self.db_manager.get_connection() as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def _vacuum(self) -> None:
        with self.db_manager.get_connection() as conn:
            conn.execute("VACUUM")

    def _optimize(self) -> None:
        with self.db_manager.get_connection() as conn:
            conn.execute("PRAGMA optimize")

    def _wal_bytes(self) -> int:
        try:
            return os.path.getsize(f"{self.db_manager.db_name}-wal")
        except OSError:
            return 0

    @staticmethod
    def _log_report(before: DatabaseStats, after: DatabaseStats, obsolete: list[str]) -> None:
        largest = sorted(after.table_rows.items(), key=lambda item: item[1], reverse=True)[:_TOP_TABLES_IN_REPORT]
        logger.info(
            "[Maintenance] Database %.2f MB (free %.2f MB, WAL %.2f MB); reclaimed %.2f MB; largest tables: %s",
            after.file_bytes / 1048576, after.free_bytes / 1048576, after.wal_bytes / 1048576,
            max(before.file_bytes - after.file_bytes, 0) / 1048576,
            ", ".join(f"{name}={rows}" for name, rows in largest),
        )
        if obsolete:
            logger.warning("[Maintenance] Objects not declared by the current schema: %s", ", ".join(obsolete))
