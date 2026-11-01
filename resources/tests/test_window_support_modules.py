# resources\tests\test_window_support_modules.py

import sys
from unittest.mock import MagicMock

from PySide6.QtCore import Qt

from backend.connections import WorkerSlot
from frontend.window.media_keys import MediaKeysHandler
from frontend.window.shutdown import ShutdownSequence
from frontend.window.session_metrics import SessionMetrics


def _metrics(provider=None):
    return SessionMetrics(provider or (lambda: {"total_command_usages": 7, "active_timers": 2}))


def test_record_message_counts_total_and_platform(qapp):
    metrics = _metrics()

    metrics.record_message("twitch")
    metrics.record_message("twitch")
    metrics.record_message("unknown")

    assert metrics.messages_processed == 3
    assert metrics.platform_messages("twitch") == 2
    assert metrics.platform_messages("unknown") == 0
    assert metrics.platform_messages("kick") == 0


def test_refresh_analytics_is_cached_unless_forced(qapp):
    provider = MagicMock(return_value={"total_command_usages": 7, "active_timers": 2})
    metrics = _metrics(provider)
    loaded = []
    metrics.analytics_loaded.connect(loaded.append)

    assert metrics.refresh_analytics() is True
    assert metrics.refresh_analytics() is True
    assert provider.call_count == 1
    assert metrics.refresh_analytics(force=True) is True
    assert provider.call_count == 2
    assert metrics.total_usages == 7
    assert metrics.active_timers == 2
    assert len(loaded) == 2


def test_refresh_analytics_reports_provider_failure(qapp):
    metrics = _metrics(MagicMock(side_effect=RuntimeError("db closed")))

    assert metrics.refresh_analytics() is False
    assert metrics.total_usages == 0


def test_metric_changes_emit_a_single_debounced_refresh(qapp):
    metrics = _metrics()
    refreshes = []
    metrics.refresh_requested.connect(lambda: refreshes.append(True))

    metrics.record_message("kick")
    metrics.record_spam_blocked()
    assert metrics.spam_blocked == 1
    assert metrics._refresh_timer.isActive()

    metrics.stop()
    assert not metrics._refresh_timer.isActive()
    assert refreshes == []


def _media_keys(music, *, platform_enabled=True, shutting_down=False, worker_factory=None):
    config = MagicMock()
    config.load_bool.return_value = platform_enabled
    slot = WorkerSlot("Worker_Global_Media_Keys", MagicMock())
    handler = MediaKeysHandler(
        music,
        config=config,
        slot=slot,
        worker_factory=worker_factory or MagicMock(),
        is_shutting_down=lambda: shutting_down,
    )
    return handler, slot


def test_media_keys_dispatch_qt_keys():
    music = MagicMock()
    handler, _slot = _media_keys(music)

    assert handler.handle_key(Qt.Key.Key_MediaStop) is True
    assert handler.handle_key(Qt.Key.Key_MediaNext) is True
    assert handler.handle_key(Qt.Key.Key_A) is False

    music.handle_play_pause.assert_called_once_with()
    music.handle_skip.assert_called_once_with()


def test_media_keys_ignore_native_events_outside_windows(monkeypatch):
    music = MagicMock()
    monkeypatch.setattr(sys, "platform", "linux")

    handler, _slot = _media_keys(music)

    assert handler.handle_native_event(b"windows_generic_MSG", 0) is False
    music.handle_play_pause.assert_not_called()


def test_worker_slot_start_stop_and_detach():
    coordinator = MagicMock()
    slot = WorkerSlot("Worker_Test", coordinator)
    worker = MagicMock()
    worker.isRunning.return_value = True

    assert slot.is_running is False
    assert slot.start(lambda: worker) is True
    worker.start.assert_called_once_with()
    assert slot.is_running is True
    assert slot.start(MagicMock()) is False

    callback = MagicMock()
    slot.stop(on_finished=callback, timeout_ms=2500)

    args, kwargs = coordinator.stop_workers.call_args
    assert args[0] == [("Worker_Test", worker)]
    assert kwargs == {"on_finished": callback, "warning_after_seconds": 2.5}
    assert slot.is_running is False
    assert slot.detach() == ("Worker_Test", None)


def test_global_media_keys_start_after_stopping_previous_worker(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    music = MagicMock()
    worker = MagicMock()
    handler, slot = _media_keys(music, worker_factory=lambda: worker)
    slot._coordinator.stop_workers.side_effect = (
        lambda _workers, on_finished=None, warning_after_seconds=0: on_finished()
    )

    handler.setup_global_keys()

    music.media_keys_state_changed.connect.assert_called_once()
    worker.play_pause_pressed.connect.assert_called_once_with(music.handle_play_pause)
    worker.skip_pressed.connect.assert_called_once_with(music.handle_skip)
    worker.stop_pressed.connect.assert_called_once_with(music.handle_play_pause)
    worker.start.assert_called_once_with()


def test_global_media_keys_do_nothing_when_disabled_or_closing(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    factory = MagicMock()
    disabled, _slot = _media_keys(MagicMock(), platform_enabled=False, worker_factory=factory)
    disabled.setup_global_keys()

    closing, closing_slot = _media_keys(MagicMock(), shutting_down=True, worker_factory=factory)
    closing.setup_global_keys()

    factory.assert_not_called()
    closing_slot._coordinator.stop_workers.assert_not_called()


def test_shutdown_sequence_runs_steps_in_order_and_survives_failures():
    calls = []
    logger = MagicMock()

    def failing():
        calls.append("release-2")
        raise RuntimeError("boom")

    sequence = ShutdownSequence(
        logger,
        stop_workers=lambda finish: (calls.append("workers"), finish()),
        release_steps=(("release one", lambda: calls.append("release-1")), ("release two", failing)),
        close_steps=(("close one", lambda: calls.append("close-1")),),
        on_complete=lambda: calls.append("complete"),
    )

    sequence.run()

    assert calls == ["workers", "release-1", "release-2", "close-1", "complete"]
    logger.exception.assert_called_once_with("[Shutdown] Failed to %s.", "release two")
