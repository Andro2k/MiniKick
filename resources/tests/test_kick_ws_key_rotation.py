# resources\tests\test_kick_ws_key_rotation.py

import json
import unittest
from unittest import mock
from backend.config import KICK_PUSHER
from backend.config.pusher_config import PusherConfig
from backend.providers.chat.kick_ws_provider import KickWebSocketManager
OLD = "32cbd69e4b950bf97679"
NEW = "34bf7a0ff419a2a775b9"


def _frame(event: str, data) -> str:
    return json.dumps({"event": event, "data": data})

class KeyRotationTest(unittest.TestCase):
    def _manager(self, keys=(NEW, OLD)) -> KickWebSocketManager:
        manager = KickWebSocketManager("us2", keys)
        manager._running = True
        return manager

    def test_config_prefers_new_key_and_keeps_old_as_fallback(self) -> None:
        self.assertIsInstance(KICK_PUSHER, PusherConfig)
        self.assertEqual(KICK_PUSHER.keys, (NEW, OLD))
        self.assertEqual(KICK_PUSHER.cluster, "us2")
        self.assertEqual(len(set(KICK_PUSHER.keys)), len(KICK_PUSHER.keys))

    def test_starts_with_the_preferred_key(self) -> None:
        self.assertEqual(self._manager().key, NEW)

    def test_pusher_error_4001_then_close_rotates_to_next_key(self) -> None:
        manager = self._manager()
        manager._on_raw_frame(mock.MagicMock(), _frame("pusher:error", '{"code": 4001, "message": "App does not exist"}'))
        manager._on_close(mock.MagicMock(), 4001, "App does not exist")
        self.assertEqual(manager.key, OLD)

    def test_pusher_error_with_dict_payload_also_rotates(self) -> None:
        manager = self._manager()
        manager._on_raw_frame(mock.MagicMock(), _frame("pusher:error", {"code": 4003, "message": "disabled"}))
        manager._on_close(mock.MagicMock(), None, None)
        self.assertEqual(manager.key, OLD)

    def test_close_code_alone_rotates(self) -> None:
        manager = self._manager()
        manager._on_close(mock.MagicMock(), 4001, "x")
        self.assertEqual(manager.key, OLD)

    def test_last_key_does_not_go_out_of_range(self) -> None:
        manager = self._manager(keys=(NEW,))
        manager._on_close(mock.MagicMock(), 4001, "x")
        self.assertEqual(manager.key, NEW)

    def test_unrelated_codes_do_not_rotate(self) -> None:
        for code in (None, 1000, 1006, 4004, 4200):
            manager = self._manager()
            manager._on_close(mock.MagicMock(), code, None)
            self.assertEqual(manager.key, NEW, f"no debía rotar con el código {code}")

    def test_error_code_is_consumed_once(self) -> None:
        manager = self._manager(keys=(NEW, OLD, "third"))
        manager._on_raw_frame(mock.MagicMock(), _frame("pusher:error", {"code": 4001}))
        manager._on_close(mock.MagicMock(), 4001, "x")
        manager._on_close(mock.MagicMock(), 1006, "x")
        self.assertEqual(manager.key, OLD)

    def test_stop_socket_resets_to_preferred_key(self) -> None:
        manager = self._manager()
        manager._on_close(mock.MagicMock(), 4001, "x")
        self.assertEqual(manager.key, OLD)
        manager.stop_socket()
        self.assertEqual(manager.key, NEW)

    def test_requires_at_least_one_key(self) -> None:
        with self.assertRaises(ValueError):
            KickWebSocketManager("us2", ())

    def test_each_connection_uses_the_current_key_in_the_url(self) -> None:
        manager = KickWebSocketManager("us2", (NEW, OLD))
        urls: list[str] = []

        def fake_app(url, **_kwargs):
            urls.append(url)
            return mock.MagicMock()

        with mock.patch("backend.providers.chat.kick_ws_provider.websocket.WebSocketApp", side_effect=fake_app):
            manager.start_socket(123)
            manager._on_close(mock.MagicMock(), 4001, "x")
            manager.start_socket(123)

        self.assertIn(f"/app/{NEW}?", urls[0])
        self.assertIn(f"/app/{OLD}?", urls[1])

class WorkerWiringTest(unittest.TestCase):
    def test_worker_passes_all_keys_to_the_socket_manager(self) -> None:
        from backend.workers.kick_chat_worker import KickChatWorker

        worker = KickChatWorker(mock.MagicMock(), mock.MagicMock(), "us2", (NEW, OLD))
        self.assertEqual(worker.chat_manager.key, NEW)
        self.assertEqual(worker.keys, (NEW, OLD))

    def test_poll_sync_worker_is_retained_until_it_finishes(self) -> None:
        from backend.workers.kick_chat_worker import KickChatWorker

        worker = KickChatWorker(mock.MagicMock(), mock.MagicMock(), "us2", (NEW, OLD))
        poll_worker = mock.MagicMock()
        poll_worker.isRunning.return_value = True
        worker._poll_sync_worker = poll_worker

        worker._stop_poll_sync_worker()

        self.assertIn(poll_worker, worker._retiring_poll_workers)
        callback = poll_worker.finished.connect.call_args.args[0]
        callback()
        self.assertNotIn(poll_worker, worker._retiring_poll_workers)
        poll_worker.deleteLater.assert_called_once_with()

if __name__ == "__main__":
    unittest.main()
