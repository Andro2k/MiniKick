import io
import logging
import sys
import threading
import types
from unittest import mock

import pytest
from PySide6.QtCore import QThread, Signal


def test_result_workers_do_not_override_qthread_finished_signal():
    from backend.workers.bug_report_worker import BugReportWorker
    from backend.workers.crash_report_worker import CrashReportWorker
    from backend.workers.music_worker import YouTubeSearchWorker
    from backend.workers.updater_worker import UpdateDownloadWorker

    assert BugReportWorker.staticMetaObject.indexOfSignal("finished(bool,QString)") == -1
    assert CrashReportWorker.staticMetaObject.indexOfSignal("finished(bool,QString)") == -1
    assert YouTubeSearchWorker.staticMetaObject.indexOfSignal("finished(bool,QString)") == -1
    assert UpdateDownloadWorker.staticMetaObject.indexOfSignal("finished(bool)") == -1


def test_search_worker_stops_after_an_in_flight_request_is_cancelled(qapp, monkeypatch):
    from backend.workers.music_worker import YouTubeSearchWorker

    class I18n:
        def get(self, key):
            return key

    request_started = threading.Event()
    release_request = threading.Event()

    class FakeYoutubeDL:
        def __init__(self, _options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def extract_info(self, *_args, **_kwargs):
            request_started.set()
            release_request.wait(timeout=2)
            return None

    monkeypatch.setitem(
        sys.modules,
        "yt_dlp",
        types.SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )
    worker = YouTubeSearchWorker("ytsearch1:test", "test", I18n())
    results = []
    worker.search_completed.connect(lambda *args: results.append(args))
    worker.start()

    assert request_started.wait(2)
    worker.requestInterruption()
    release_request.set()
    assert worker.wait(2000)
    qapp.processEvents()
    assert worker.song_entry is None
    assert results == []


def test_music_provider_cancels_and_retains_active_search_until_thread_finishes(qapp, monkeypatch):
    import backend.providers.music.youtube_provider as music_module

    started = threading.Event()

    class BlockingSearchWorker(QThread):
        search_completed = Signal(bool, str)

        def __init__(self, *_args, **_kwargs):
            super().__init__()
            self.song_entry = {
                "title": "test song",
                "artist": "test artist",
                "url": "https://example.test/song",
            }

        def run(self):
            started.set()
            while not self.isInterruptionRequested():
                self.msleep(5)
            self.search_completed.emit(True, "completed after cancellation")

    monkeypatch.setattr(music_module, "YouTubeSearchWorker", BlockingSearchWorker)
    with (
        mock.patch.object(music_module, "QMediaPlayer") as player_cls,
        mock.patch.object(music_module, "QAudioOutput"),
        mock.patch("PySide6.QtMultimedia.QMediaDevices"),
        mock.patch("backend.database.MusicCacheManager"),
    ):
        provider = music_module.YouTubeMusicProvider(i18n=mock.Mock())
        provider._get_cached_search = mock.Mock(return_value=None)
        worker_finished_callback = mock.Mock()
        provider.add_to_queue("test song", callback=worker_finished_callback)

        worker = provider._search_workers[0]
        assert worker in music_module._ACTIVE_SEARCH_WORKERS
        assert started.wait(1)
        provider.shutdown()
        assert worker.isInterruptionRequested()
        assert worker.wait(2000)
        qapp.processEvents()

        assert worker not in provider._search_workers
        assert worker not in provider._search_contexts
        assert worker not in music_module._ACTIVE_SEARCH_WORKERS
        assert provider.queue == []
        worker_finished_callback.assert_not_called()
        player_cls.return_value.stop.assert_called_once_with()


def test_music_search_result_is_processed_in_provider_thread(qapp, monkeypatch):
    import backend.providers.music.youtube_provider as music_module

    song_entry = {
        "title": "test song",
        "artist": "test artist",
        "url": "https://example.test/song",
    }

    class CompletingSearchWorker(QThread):
        search_completed = Signal(bool, str)

        def __init__(self, *_args, **_kwargs):
            super().__init__()
            self.song_entry = dict(song_entry)

        def run(self):
            self.search_completed.emit(True, "completed")

    monkeypatch.setattr(music_module, "YouTubeSearchWorker", CompletingSearchWorker)
    with (
        mock.patch.object(music_module, "QMediaPlayer"),
        mock.patch.object(music_module, "QAudioOutput"),
        mock.patch("PySide6.QtMultimedia.QMediaDevices"),
        mock.patch("backend.database.MusicCacheManager"),
    ):
        provider = music_module.YouTubeMusicProvider(i18n=mock.Mock())
        provider._get_cached_search = mock.Mock(return_value=None)
        provider._play_next = mock.Mock()
        callback_results = []
        callback_thread_ids = []
        main_thread_id = threading.get_ident()
        provider.add_to_queue(
            "test song",
            callback=lambda *result: (
                callback_results.append(result),
                callback_thread_ids.append(threading.get_ident()),
            ),
        )

        worker = provider._search_workers[0]
        assert worker.wait(2000)
        qapp.processEvents()

        assert provider.queue[0]["title"] == song_entry["title"]
        assert callback_results == [(True, "completed")]
        assert callback_thread_ids == [main_thread_id]
        provider.shutdown()


def test_container_shutdown_attempts_each_component_once_even_if_one_fails(caplog):
    from backend.core.app_container_core import AppContainerCore

    container = AppContainerCore.__new__(AppContainerCore)
    container._is_shutdown = False
    container._music_provider = mock.Mock()
    container.tts_manager = mock.Mock()
    container.tts_manager.shutdown.side_effect = RuntimeError("TTS shutdown failed")
    container.overlay_server = mock.Mock()

    with caplog.at_level(logging.ERROR, logger="minikick.core.app_container"):
        container.shutdown()
        container.shutdown()

    container._music_provider.shutdown.assert_called_once_with()
    container.tts_manager.shutdown.assert_called_once_with()
    container.overlay_server.stop.assert_called_once_with()
    assert "Failed to stop component Mock" in caplog.text


def test_tts_shutdown_is_idempotent_and_stops_queue_threads():
    from backend.services.chat.tts_service import TTSManager

    manager = TTSManager()
    manager.shutdown()
    manager.shutdown()
    manager.say("ignored after shutdown")
    manager._downloader_thread.join(timeout=2)
    manager._thread.join(timeout=2)

    assert not manager._downloader_thread.is_alive()
    assert not manager._thread.is_alive()
    assert manager.text_queue.empty()


def test_resetting_log_handlers_flushes_and_closes_them():
    from backend.core.app_logger_core import _reset_handlers

    class TrackingHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.flush_count = 0
            self.close_count = 0

        def flush(self):
            self.flush_count += 1

        def close(self):
            self.close_count += 1
            super().close()

    logger = logging.Logger("test.reset.handlers")
    handler = TrackingHandler()
    logger.addHandler(handler)

    _reset_handlers(logger)

    assert logger.handlers == []
    assert handler.flush_count == 1
    assert handler.close_count == 1


def test_flush_failures_are_reported_to_original_stderr(monkeypatch):
    from backend.core import app_logger_core

    class FailingHandler(logging.Handler):
        def flush(self):
            raise OSError("flush failed")

    stderr = io.StringIO()
    root_logger = logging.getLogger()
    monkeypatch.setattr(root_logger, "handlers", [FailingHandler()])
    monkeypatch.setattr(sys, "__stderr__", stderr)
    monkeypatch.setattr(app_logger_core, "_fault_file_handle", None)

    app_logger_core.flush_all_logs()

    assert "Failed to flush handler FailingHandler: flush failed" in stderr.getvalue()
