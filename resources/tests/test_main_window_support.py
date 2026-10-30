# resources\tests\test_main_window_support.py

import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer

from frontend.main_window import MainWindowCore
from frontend.main_window_views import MainWindowViewFactory
from frontend.recent_redemptions import RecentRedemptionCache
from frontend.worker_shutdown import WorkerShutdownCoordinator


class _CooperativeWorker(QThread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.started_event = threading.Event()

    def run(self):
        self.started_event.set()
        self._stop_event.wait()

    def stop(self):
        self._stop_event.set()


def test_recent_redemptions_are_deduplicated_and_bounded():
    cache = RecentRedemptionCache(maxlen=2)

    assert cache.contains_or_add("first") is False
    assert cache.contains_or_add("first") is True
    assert cache.contains_or_add("second") is False
    assert cache.contains_or_add("third") is False
    assert cache.contains_or_add("first") is False


def test_view_factory_creates_and_attaches_a_view_only_once(qapp, monkeypatch):
    import frontend.main_window_views as views_module

    view = MagicMock()
    chat_view_class = MagicMock(return_value=view)
    import_module = MagicMock(return_value=SimpleNamespace(ChatView=chat_view_class))
    monkeypatch.setattr(views_module.importlib, "import_module", import_module)
    content_stack = MagicMock()
    content_stack.indexOf.return_value = 0
    window = SimpleNamespace(
        _instantiated_views={},
        content_stack=content_stack,
        i18n=MagicMock(),
        overlay_server=MagicMock(),
        chat_controller=MagicMock(),
        spam_controller=MagicMock(),
    )
    factory = MainWindowViewFactory(window)

    assert factory.get_or_create("Chat") is view
    assert factory.get_or_create("Chat") is view
    import_module.assert_called_once_with(".views.chat_view", package="frontend")
    chat_view_class.assert_called_once_with(window.i18n, parent=content_stack)
    content_stack.addWidget.assert_called_once_with(view)
    window.chat_controller.attach_view.assert_called_once_with(view)


def test_views_package_defers_importing_unselected_views():
    project_root = Path(__file__).resolve().parents[2]
    code = (
        "import sys; import frontend.views; "
        "assert 'frontend.views.chat_view' not in sys.modules; "
        "from frontend.views import DashboardView; "
        "assert 'frontend.views.dashboard_view' in sys.modules; "
        "assert 'frontend.views.chat_view' not in sys.modules"
    )

    subprocess.run(
        [sys.executable, "-c", code],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )


def test_worker_shutdown_does_not_block_the_event_loop(qapp):
    parent = QObject()
    retiring_workers = set()
    coordinator = WorkerShutdownCoordinator(
        parent,
        logging.getLogger("test.worker_shutdown"),
        retiring_workers,
    )
    worker = _CooperativeWorker()
    worker.start()
    assert worker.started_event.wait(timeout=1)

    event_loop = QEventLoop()
    completed = []
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(event_loop.quit)
    timeout.start(2000)

    started_at = time.perf_counter()
    coordinator.stop_workers(
        [("test worker", worker)],
        on_finished=lambda: (completed.append(True), event_loop.quit()),
    )
    request_elapsed = time.perf_counter() - started_at
    event_loop.exec()

    assert request_elapsed < 0.1
    assert completed == [True]
    assert not worker.isRunning()
    assert worker not in retiring_workers


def test_worker_shutdown_ignores_already_deleted_qthread(caplog):
    parent = QObject()
    retiring_workers = set()
    coordinator = WorkerShutdownCoordinator(
        parent,
        logging.getLogger("test.worker_shutdown"),
        retiring_workers,
    )
    
    worker = MagicMock(spec=QThread)
    worker.isRunning.side_effect = RuntimeError("Internal C++ object already deleted")
    
    signal_mock = MagicMock()
    signal_mock.connect.side_effect = RuntimeError("Signal source has been deleted")
    signal_mock.disconnect.side_effect = RuntimeError("Signal source has been deleted")
    worker.finished = signal_mock

    with caplog.at_level(logging.WARNING, logger="test.worker_shutdown"):
        coordinator.stop_workers([("deleted worker", worker)])

    assert not caplog.records
    assert worker not in retiring_workers


def test_whats_new_fetch_replaces_already_deleted_worker(monkeypatch):
    import backend.workers

    stale_worker = MagicMock(spec=QThread)
    stale_worker.isRunning.side_effect = RuntimeError("Internal C++ object already deleted")

    replacement = SimpleNamespace(
        highlights_fetched=MagicMock(),
        finished=MagicMock(),
        deleteLater=MagicMock(),
        start=MagicMock(),
    )
    worker_factory = MagicMock(return_value=replacement)
    monkeypatch.setattr(backend.workers, "WhatsNewWorker", worker_factory)
    
    window = SimpleNamespace(
        _is_shutting_down=False,
        _is_window_closing=False,
        _whats_new_worker=stale_worker,
        _is_worker_running=MainWindowCore._is_worker_running,
        app_version="1.6.5",
        _on_remote_whats_new_fetched=MagicMock(),
    )

    MainWindowCore._fetch_remote_whats_new_if_needed(window)

    worker_factory.assert_called_once_with("1.6.5", parent=window)
    replacement.start.assert_called_once_with()
    assert window._whats_new_worker is replacement