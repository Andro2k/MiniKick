# resources\tests\test_worker_and_core_lifecycle.py

import io
import logging
import sys
import threading
import types
from unittest import mock
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


def test_cooperative_sleep_breaks_immediately_on_interruption(qapp):
    from backend.utils.worker_utils import cooperative_sleep

    fake_worker = types.SimpleNamespace(_is_stopped=True)
    assert cooperative_sleep(fake_worker, duration_seconds=5.0, step_ms=10) is False

    started_event = threading.Event()
    results = []

    class SleepWorker(QThread):
        def run(self):
            started_event.set()
            results.append(cooperative_sleep(self, duration_seconds=5.0, step_ms=10))

    worker = SleepWorker()
    worker.start()
    assert started_event.wait(1)
    worker.requestInterruption()
    assert worker.wait(1000)
    assert results == [False]


def test_chat_and_reward_workers_stop_sets_interruption_and_quit():
    from backend.workers.kick_chat_worker import KickChatWorker, KickPollSyncWorker
    from backend.workers.twitch_chat_worker import TwitchChatWorker
    from backend.workers.twitch_rewards_worker import TwitchRewardWorker

    i18n_mock = mock.Mock()
    api_mock = mock.Mock()
    api_mock.fetch_active_poll.return_value = None

    poll_worker = KickPollSyncWorker(api_mock, "test_channel", interval_ms=500)
    poll_worker.start()
    poll_worker.stop()
    assert poll_worker.isInterruptionRequested()
    assert poll_worker._is_stopped is True
    assert poll_worker.wait(1000)

    kick_worker = KickChatWorker(i18n_mock, api_mock, "us2", ("key1",))
    kick_worker.start()
    kick_worker.stop()
    assert kick_worker.isInterruptionRequested()
    assert kick_worker._is_stopped is True
    assert kick_worker.wait(1000)

    twitch_worker = TwitchChatWorker(channel_name="", oauth_token="")
    twitch_worker.start()
    twitch_worker.stop()
    assert twitch_worker.isInterruptionRequested()
    assert twitch_worker._is_stopped is True
    assert twitch_worker.wait(1000)

    twitch_rewards = TwitchRewardWorker(i18n_mock, mock.Mock(), "cid", "bid")
    twitch_rewards.start()
    twitch_rewards.stop()
    assert twitch_rewards.isInterruptionRequested()
    assert twitch_rewards._running is False
    assert twitch_rewards.wait(1000)


def test_voice_fetcher_worker_cleans_up_com_apartment(monkeypatch):
    import sys
    from backend.workers.voice_worker import VoiceFetcherWorker

    fake_pythoncom = mock.MagicMock()
    monkeypatch.setitem(sys.modules, "pythoncom", fake_pythoncom)
    monkeypatch.setattr(sys, "platform", "win32")

    tts_mock = mock.Mock()
    tts_mock.get_available_voices.return_value = ["Voice 1"]

    worker = VoiceFetcherWorker(tts_mock, "windows_sapi")
    worker.run()

    fake_pythoncom.CoInitialize.assert_called_once()
    fake_pythoncom.CoUninitialize.assert_called_once()


def test_ephemeral_workers_suppress_signals_when_interrupted():
    from backend.workers.rewards_worker import FetchRewardsWorker
    from backend.workers.updater_worker import UpdateCheckWorker

    fetch_started = threading.Event()
    release_fetch = threading.Event()

    def fake_fetch(*_args, **_kwargs):
        fetch_started.set()
        release_fetch.wait(timeout=2)
        return {"data": [{"title": "Reward 1"}]}

    api_mock = mock.Mock()
    api_mock.fetch_channel_rewards.side_effect = fake_fetch
    rewards_worker = FetchRewardsWorker(api_mock, platform="kick")

    rewards_received = []
    rewards_worker.rewards_fetched.connect(lambda *args: rewards_received.append(args))
    rewards_worker.start()

    assert fetch_started.wait(2)
    rewards_worker.requestInterruption()
    release_fetch.set()
    assert rewards_worker.wait(2000)
    assert rewards_received == []

    check_started = threading.Event()
    release_check = threading.Event()

    def fake_check(*_args, **_kwargs):
        check_started.set()
        release_check.wait(timeout=2)
        return {"version": "1.7.0"}

    manager_mock = mock.Mock()
    manager_mock.check_for_updates.side_effect = fake_check
    updater_worker = UpdateCheckWorker(manager_mock)

    updates_received = []
    updater_worker.update_found.connect(lambda *args: updates_received.append(args))
    updater_worker.start()

    assert check_started.wait(2)
    updater_worker.requestInterruption()
    release_check.set()
    assert updater_worker.wait(2000)
    assert updates_received == []
