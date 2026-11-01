# resources\tests\test_window_support_modules.py

import sys
from unittest.mock import MagicMock

from PySide6.QtCore import Qt

from frontend.window.media_keys import MediaKeysHandler
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


def test_media_keys_dispatch_qt_keys():
    music = MagicMock()
    handler = MediaKeysHandler(music)

    assert handler.handle_key(Qt.Key.Key_MediaStop) is True
    assert handler.handle_key(Qt.Key.Key_MediaNext) is True
    assert handler.handle_key(Qt.Key.Key_A) is False

    music.handle_play_pause.assert_called_once_with()
    music.handle_skip.assert_called_once_with()


def test_media_keys_ignore_native_events_outside_windows(monkeypatch):
    music = MagicMock()
    monkeypatch.setattr(sys, "platform", "linux")

    assert MediaKeysHandler(music).handle_native_event(b"windows_generic_MSG", 0) is False
    music.handle_play_pause.assert_not_called()
