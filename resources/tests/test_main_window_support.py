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
from frontend.window.whats_new import WhatsNewPresenter
from backend.connections import WorkerShutdownCoordinator, WorkerSlot


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


def test_startup_connection_toast_suppression_is_consumed_once():
    window = SimpleNamespace(_startup_silent_connections={"kick", "twitch"})

    assert MainWindowCore._consume_startup_silent_connection(window, "kick") is True
    assert MainWindowCore._consume_startup_silent_connection(window, "kick") is False
    assert MainWindowCore._consume_startup_silent_connection(window, "twitch") is True


def test_window_runtime_flags_are_initialized_in_one_place():
    window = SimpleNamespace()

    MainWindowCore._init_flags(window)

    assert window._is_shutting_down is False
    assert window._cleanup_complete is False
    assert window._quit_requested is False
    assert window._startup_silent_connections == set()
    assert window._applied_font_size is None
    assert not hasattr(window, "_is_window_closing")


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
        settings_storage=MagicMock(),
        overlay_server=MagicMock(),
        chat_controller=MagicMock(),
        spam_controller=MagicMock(),
    )
    factory = MainWindowViewFactory(window)

    assert factory.get_or_create("Chat") is view
    assert factory.get_or_create("Chat") is view
    import_module.assert_called_once_with(".views.chat_view", package="frontend")
    chat_view_class.assert_called_once_with(
        window.i18n,
        parent=content_stack,
        config=window.settings_storage,
    )
    content_stack.addWidget.assert_called_once_with(view)
    window.chat_controller.attach_view.assert_called_once_with(view)


def test_settings_view_routes_live_chat_buttons_to_their_connections(qapp, monkeypatch):
    import frontend.main_window_views as views_module

    view = MagicMock()
    settings_view_class = MagicMock(return_value=view)
    monkeypatch.setattr(
        views_module,
        "_load_view_class",
        MagicMock(return_value=settings_view_class),
    )
    window = SimpleNamespace(
        _instantiated_views={},
        content_stack=MagicMock(),
        i18n=MagicMock(),
        youtube=MagicMock(name="youtube"),
        tiktok=MagicMock(name="tiktok"),
        platform_connections=SimpleNamespace(
            on_twitch_integration_button_clicked=MagicMock(),
            on_live_chat_button_clicked=MagicMock(),
            update_integrations_status_ui=MagicMock(),
        ),
        settings_controller=MagicMock(),
    )
    factory = MainWindowViewFactory(window)

    assert factory.get_or_create("Settings") is view

    view.youtube_integration_clicked.connect.call_args.args[0]()
    view.tiktok_integration_clicked.connect.call_args.args[0]()

    window.platform_connections.on_live_chat_button_clicked.assert_any_call(window.youtube)
    window.platform_connections.on_live_chat_button_clicked.assert_any_call(window.tiktok)
    settings_view_class.assert_called_once_with(window.i18n, parent=window.content_stack)
    window.settings_controller.attach_view.assert_called_once_with(view)


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
        error_occurred=MagicMock(),
        finished=MagicMock(),
        deleteLater=MagicMock(),
        start=MagicMock(),
    )
    worker_factory = MagicMock(return_value=replacement)
    monkeypatch.setattr(backend.workers, "WhatsNewWorker", worker_factory)

    slot = WorkerSlot("Worker_Whats_New", MagicMock())
    slot.start(lambda: stale_worker)
    presenter = WhatsNewPresenter(
        parent="window",
        service=MagicMock(),
        sidebar=MagicMock(),
        i18n=MagicMock(),
        app_version="1.6.5",
        slot=slot,
        is_shutting_down=lambda: False,
    )

    presenter.fetch_remote_if_needed()

    worker_factory.assert_called_once_with("1.6.5", parent="window")
    replacement.start.assert_called_once_with()
    assert slot.detach() == ("Worker_Whats_New", replacement)
