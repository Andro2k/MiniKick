# resources\tests\test_chat_performance_paths.py

import threading
import time

import pytest
from PySide6.QtCore import QCoreApplication

from backend.database.database_manager import DatabaseManager
from backend.services.chat.spam_service import SpamService
from backend.services.overlay.overlay_ws_client import WebSocketClient
from backend.utils.io_background import BoundedBackgroundWorker, flush_network_io
from frontend.window.session_metrics import SessionMetrics


def _pump(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def test_network_worker_runs_jobs_in_order_off_the_caller_thread():
    worker = BoundedBackgroundWorker("TestNetworkWorker")
    seen = []
    for i in range(5):
        worker.submit(lambda n=i: seen.append((n, threading.current_thread().name)))
    assert worker.flush(2.0)
    assert [n for n, _ in seen] == [0, 1, 2, 3, 4]
    assert all(name == "TestNetworkWorker" for _, name in seen)


def test_network_worker_drops_new_jobs_when_backlog_is_full():
    worker = BoundedBackgroundWorker("TestNetworkWorkerFull", max_pending=2)
    gate = threading.Event()
    started = threading.Event()

    def blocker():
        started.set()
        gate.wait(2.0)

    assert worker.submit(blocker)
    assert started.wait(1.0)
    assert worker.submit(lambda: None)
    assert worker.submit(lambda: None)
    assert worker.submit(lambda: None) is False
    gate.set()
    assert worker.flush(2.0)


class _FakeSpamStorage:
    def __init__(self, filters):
        self._filters = filters

    def load_all(self):
        return self._filters


class _SlowApi:
    def __init__(self):
        self.calls = []

    def delete_chat_message(self, msg_id):
        time.sleep(0.3)
        self.calls.append((msg_id, threading.current_thread().name))
        return True


def test_spam_penalty_http_does_not_block_the_calling_thread():
    api = _SlowApi()
    service = SpamService(_FakeSpamStorage({}), api_client=api)
    config = {"penalty": "delete", "duration": 1}

    started = time.perf_counter()
    service._apply_penalty("user", 1, "msg-1", config, "caps_protection", "HOLA", platform="kick")
    elapsed = time.perf_counter() - started

    assert elapsed < 0.15
    assert flush_network_io(3.0)
    assert api.calls == [("msg-1", "NetworkIOWorker")]


def test_repetition_history_is_tracked_per_platform():
    filters = {
        "repetition_protection": {
            "is_active": True, "max_amount": 1, "penalty": "delete",
            "apply_kick": True, "apply_twitch": True,
        }
    }
    service = SpamService(_FakeSpamStorage(filters))

    assert service.is_spam("same_name", "hola mundo", [], "m1", 1, platform="kick") is False
    assert service.is_spam("same_name", "hola mundo", [], "m2", 1, platform="twitch") is False
    assert service.is_spam("same_name", "hola mundo", [], "m3", 1, platform="kick") is True
    flush_network_io(2.0)


class _FakeSocket:
    def __init__(self):
        self.shutdown_called = False

    def shutdown(self, _how):
        self.shutdown_called = True


class _BlockingWfile:
    def __init__(self):
        self.release = threading.Event()

    def write(self, _data):
        self.release.wait(5.0)

    def flush(self):
        pass


class _RecordingWfile:
    def __init__(self):
        self.frames = []

    def write(self, data):
        self.frames.append(bytes(data))

    def flush(self):
        pass


class _FakeHandler:
    def __init__(self, wfile):
        self.wfile = wfile
        self.rfile = None
        self.connection = _FakeSocket()


def test_ws_send_text_never_blocks_on_a_stalled_consumer():
    wfile = _BlockingWfile()
    handler = _FakeHandler(wfile)
    client = WebSocketClient(handler, "chat", "tok")

    started = time.perf_counter()
    for i in range(700):
        client.send_text(f'{{"n": {i}}}')
    elapsed = time.perf_counter() - started
    wfile.release.set()

    assert elapsed < 1.0
    assert client.closed is True
    assert handler.connection.shutdown_called is True


def test_ws_frames_are_delivered_in_order():
    wfile = _RecordingWfile()
    client = WebSocketClient(_FakeHandler(wfile), "chat", "tok")

    for i in range(3):
        client.send_text(f"msg{i}")

    assert _pump(lambda: len(wfile.frames) == 3)
    assert [f[2:] for f in wfile.frames] == [b"msg0", b"msg1", b"msg2"]
    client.close()


def test_session_metrics_loads_analytics_off_the_ui_thread_and_coalesces(qapp, monkeypatch):
    monkeypatch.setattr(SessionMetrics, "_ANALYTICS_RERUN_DELAY_MS", 30)
    threads = []

    def provider():
        threads.append(threading.current_thread())
        time.sleep(0.05)
        return {"total_command_usages": 7, "active_timers": 2}

    metrics = SessionMetrics(provider)
    loaded = []
    metrics.analytics_loaded.connect(loaded.append)

    for _ in range(5):
        metrics.request_analytics_refresh()

    assert _pump(lambda: len(threads) == 2 and len(loaded) == 2)
    assert all(t is not threading.main_thread() for t in threads)
    assert metrics.total_usages == 7 and metrics.active_timers == 2
    metrics.stop()


def test_db_busy_timeout_is_short_on_the_ui_thread_and_long_in_workers(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    manager = DatabaseManager("busy_timeout_test.db")

    with manager.get_connection() as conn:
        ui_value = conn.execute("PRAGMA busy_timeout").fetchone()[0]

    result = {}

    def worker():
        with manager.get_connection() as conn:
            result["value"] = conn.execute("PRAGMA busy_timeout").fetchone()[0]

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(5.0)

    assert ui_value == 5000
    assert result["value"] == 30000
