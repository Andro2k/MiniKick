import logging
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer

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
    monkeypatch.setattr(views_module, "ChatView", MagicMock(return_value=view))
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
    content_stack.addWidget.assert_called_once_with(view)
    window.chat_controller.attach_view.assert_called_once_with(view)


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
