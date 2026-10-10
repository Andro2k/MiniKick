# tests\test_migrations.py

import os
import sqlite3
import tempfile
import unittest
from unittest import mock


class MigrationAtomicityTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._env = mock.patch.dict(os.environ, {"LOCALAPPDATA": self._tmp.name})
        self._env.start()
        from backend.database import database_manager as dbm
        dbm.DatabaseManager._initialized_dbs.clear()
        self.dbm = dbm

    def tearDown(self) -> None:
        self._env.stop()
        self._tmp.cleanup()

    def _version(self, manager) -> int:
        with manager.get_connection() as conn:
            return conn.execute("PRAGMA user_version").fetchone()[0]

    def test_failed_migration_rolls_back_and_keeps_version(self) -> None:
        manager = self.dbm.DatabaseManager("t.db")
        before = self._version(manager)

        def failing(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE should_not_exist (id INTEGER)")
            raise sqlite3.OperationalError("boom")

        with mock.patch.object(self.dbm, "MIGRATIONS", [(before + 1, failing)]):
            with self.assertRaises(sqlite3.OperationalError):
                manager._apply_migrations()

        self.assertEqual(self._version(manager), before)
        with manager.get_connection() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE name='should_not_exist'"
            ).fetchone()
        self.assertIsNone(row)

    def test_successful_migration_advances_version(self) -> None:
        manager = self.dbm.DatabaseManager("t.db")
        before = self._version(manager)

        def ok(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE migrated_ok (id INTEGER)")

        with mock.patch.object(self.dbm, "MIGRATIONS", [(before + 1, ok)]):
            manager._apply_migrations()

        self.assertEqual(self._version(manager), before + 1)


if __name__ == "__main__":
    unittest.main()