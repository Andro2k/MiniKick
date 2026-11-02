# resources\tests\test_live_chat_offline_autostart.py

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QObject, Signal

from backend.connections import TikTokConnection, YouTubeConnection
from backend.services.system import TranslationService
from frontend.main_window import MainWindowCore


class _SettingsStorage:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def load_bool(self, key, default=False):
        return self.values.get(key, default)

    def save_bool(self, key, value):
        self.values[key] = value

    def load_string(self, key, default=""):
        return self.values.get(key, default)

    def save_string(self, key, value):
        self.values[key] = value


class _ChatWorker(QObject):
    message_received = Signal(object)
    error_occurred = Signal(str)
    connection_success = Signal(object)
    connection_lost = Signal()
    instances = []

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        self.started = False
        _ChatWorker.instances.append(self)

    def start(self):
        self.started = True


@pytest.fixture(autouse=True)
def _fake_workers(monkeypatch):
    import backend.workers

    _ChatWorker.instances = []
    monkeypatch.setattr(backend.workers, "YouTubeChatWorker", _ChatWorker)
    monkeypatch.setattr(backend.workers, "TikTokChatWorker", _ChatWorker)


def _connections(settings, *, shutting_down=False, defer_stop=False):
    deferred = []

    def stop_workers(_workers, on_finished=None, warning_after_seconds=0):
        if on_finished is None:
            return
        if defer_stop:
            deferred.append(on_finished)
        else:
            on_finished()

    coordinator = SimpleNamespace(stop_workers=stop_workers)
    i18n = TranslationService(default_lang="es")

    def build(connection_class):
        return connection_class(
            config=settings,
            i18n=i18n,
            coordinator=coordinator,
            is_shutting_down=lambda: shutting_down,
        )

    return build(YouTubeConnection), build(TikTokConnection), deferred, i18n


def test_autostart_skips_streams_saved_as_offline(qapp):
    settings = _SettingsStorage({
        YouTubeConnection.offline_setting_key: True,
        TikTokConnection.offline_setting_key: True,
    })
    youtube, tiktok, _deferred, _i18n = _connections(settings)
    youtube.connect_channel = Mock()
    tiktok.connect_channel = Mock()
    window = SimpleNamespace(_is_shutting_down=False, logger=Mock())

    MainWindowCore._autostart_live_chat(window, youtube, "youtube-channel")
    MainWindowCore._autostart_live_chat(window, tiktok, "tiktok-channel")

    youtube.connect_channel.assert_not_called()
    tiktok.connect_channel.assert_not_called()


def test_autostart_connects_without_clearing_offline_suppression(qapp):
    settings = _SettingsStorage()
    youtube, _tiktok, _deferred, _i18n = _connections(settings)
    youtube.connect_channel = Mock()
    window = SimpleNamespace(_is_shutting_down=False, logger=Mock(), _startup_silent_connections=set())

    MainWindowCore._autostart_live_chat(window, youtube, "youtube-channel")

    youtube.connect_channel.assert_called_once_with("youtube-channel", manual=False)
    assert window._startup_silent_connections == {"youtube"}


def test_offline_errors_are_remembered_for_both_platforms(qapp):
    settings = _SettingsStorage()
    youtube, tiktok, _deferred, i18n = _connections(settings)
    reported = []
    youtube.error_reported.connect(lambda msg, offline: reported.append(("youtube", offline)))
    tiktok.error_reported.connect(lambda msg, offline: reported.append(("tiktok", offline)))

    youtube.connect_channel("youtube-channel")
    tiktok.connect_channel("tiktok-channel")
    youtube_offline = i18n.get("logs.youtube.video_not_found").replace("{target}", "youtube-channel")
    tiktok_offline = i18n.get("logs.tiktok.stream_offline").replace("{unique_id}", "tiktok-channel")
    youtube_worker, tiktok_worker = _ChatWorker.instances
    youtube_worker.error_occurred.emit(youtube_offline)
    tiktok_worker.error_occurred.emit(tiktok_offline)

    assert settings.values[YouTubeConnection.offline_setting_key] is True
    assert settings.values[TikTokConnection.offline_setting_key] is True
    assert reported == [("youtube", True), ("tiktok", True)]
    assert youtube.is_connected is False


def test_non_offline_errors_do_not_set_the_offline_flag(qapp):
    settings = _SettingsStorage()
    youtube, _tiktok, _deferred, _i18n = _connections(settings)
    reported = []
    youtube.error_reported.connect(lambda msg, offline: reported.append((msg, offline)))

    youtube.connect_channel("youtube-channel")
    _ChatWorker.instances[0].error_occurred.emit("boom")

    assert settings.values[YouTubeConnection.offline_setting_key] is False
    assert reported == [("boom", False)]


def test_manual_connect_clears_offline_suppression(qapp):
    settings = _SettingsStorage({
        YouTubeConnection.offline_setting_key: True,
        TikTokConnection.offline_setting_key: True,
    })
    youtube, tiktok, _deferred, _i18n = _connections(settings)
    connecting = []
    youtube.connecting.connect(lambda: connecting.append("youtube"))

    youtube.connect_channel("youtube-channel")
    tiktok.connect_channel("@tiktok-channel")

    assert settings.values[YouTubeConnection.offline_setting_key] is False
    assert settings.values[TikTokConnection.offline_setting_key] is False
    assert [worker.started for worker in _ChatWorker.instances] == [True, True]
    assert _ChatWorker.instances[1].kwargs["target_channel"] == "tiktok-channel"
    assert connecting == ["youtube"]


def test_tiktok_ignores_blank_targets(qapp):
    settings = _SettingsStorage({TikTokConnection.offline_setting_key: True})
    _youtube, tiktok, _deferred, _i18n = _connections(settings)

    tiktok.connect_channel("  @ ")

    assert _ChatWorker.instances == []
    assert settings.values[TikTokConnection.offline_setting_key] is True


def test_connection_success_persists_target_and_notifies(qapp):
    settings = _SettingsStorage()
    youtube, _tiktok, _deferred, _i18n = _connections(settings)
    events = []
    youtube.state_changed.connect(lambda: events.append("state"))
    youtube.connected.connect(lambda name: events.append(("connected", name)))

    youtube.connect_channel("youtube-channel")
    _ChatWorker.instances[0].connection_success.emit({"channel": "yt-id", "title": "Directo"})

    assert youtube.is_connected is True
    assert youtube.channel == "Directo"
    assert settings.values[YouTubeConnection.target_setting_key] == "yt-id"
    assert events == ["state", ("connected", "Directo")]


def test_connection_lost_keeps_the_channel_but_marks_disconnected(qapp):
    settings = _SettingsStorage()
    youtube, _tiktok, _deferred, _i18n = _connections(settings)

    youtube.connect_channel("youtube-channel")
    worker = _ChatWorker.instances[0]
    worker.connection_success.emit({"channel": "yt-id"})
    worker.connection_lost.emit()

    assert youtube.is_connected is False
    assert youtube.channel == "yt-id"


def test_disconnect_clears_state_and_saved_target(qapp):
    settings = _SettingsStorage({TikTokConnection.target_setting_key: "old"})
    _youtube, tiktok, _deferred, _i18n = _connections(settings)
    disconnected = []
    tiktok.disconnected.connect(lambda: disconnected.append(True))

    tiktok.connect_channel("tiktok-channel")
    _ChatWorker.instances[0].connection_success.emit({"unique_id": "tiktok-channel"})
    tiktok.disconnect_channel()

    assert tiktok.is_connected is False
    assert tiktok.channel == ""
    assert settings.values[TikTokConnection.target_setting_key] == ""
    assert disconnected == [True]


def test_stale_connect_does_not_start_a_worker_after_disconnect(qapp):
    settings = _SettingsStorage()
    youtube, _tiktok, deferred, _i18n = _connections(settings, defer_stop=True)

    youtube.connect_channel("youtube-channel")
    youtube.disconnect_channel()
    for callback in deferred:
        callback()

    assert _ChatWorker.instances == []


def test_shutdown_prevents_new_connections(qapp):
    settings = _SettingsStorage()
    youtube, _tiktok, _deferred, _i18n = _connections(settings, shutting_down=True)

    youtube.connect_channel("youtube-channel")

    assert _ChatWorker.instances == []
