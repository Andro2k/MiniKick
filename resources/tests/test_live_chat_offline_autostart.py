from types import SimpleNamespace
from unittest.mock import Mock

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


class _Signal:
    def connect(self, _callback):
        pass


class _ChatWorker:
    def __init__(self, **_kwargs):
        self.connection_success = _Signal()
        self.connection_lost = _Signal()
        self.error_occurred = _Signal()
        self.message_received = _Signal()

    def start(self):
        pass


def _window(settings_storage, i18n):
    return SimpleNamespace(
        SETTING_YOUTUBE_OFFLINE=MainWindowCore.SETTING_YOUTUBE_OFFLINE,
        SETTING_TIKTOK_OFFLINE=MainWindowCore.SETTING_TIKTOK_OFFLINE,
        settings_storage=settings_storage,
        logger=Mock(),
        container=SimpleNamespace(i18n=i18n),
        toast=SimpleNamespace(show_toast=Mock()),
        _safe_stop_worker=Mock(),
        _update_integrations_status_ui=Mock(),
        _route_incoming_message=Mock(),
        _is_window_closing=False,
    )


def test_offline_autostart_is_suppressed_for_both_platforms(qapp):
    i18n = TranslationService(default_lang="es")
    settings = _SettingsStorage({
        MainWindowCore.SETTING_YOUTUBE_OFFLINE: True,
        MainWindowCore.SETTING_TIKTOK_OFFLINE: True,
    })
    window = _window(settings, i18n)
    window._handle_youtube_connect = Mock()
    window._handle_tiktok_connect = Mock()

    MainWindowCore._autostart_youtube(window, "youtube-channel")
    MainWindowCore._autostart_tiktok(window, "tiktok-channel")

    window._handle_youtube_connect.assert_not_called()
    window._handle_tiktok_connect.assert_not_called()


def test_offline_errors_are_remembered_for_both_platforms(qapp):
    i18n = TranslationService(default_lang="es")
    settings = _SettingsStorage()
    window = _window(settings, i18n)

    youtube_offline = i18n.get("logs.youtube.video_not_found").replace(
        "{target}", "youtube-channel"
    )
    tiktok_offline = i18n.get("logs.tiktok.stream_offline").replace(
        "{unique_id}", "tiktok-channel"
    )

    MainWindowCore._on_youtube_error(window, youtube_offline)
    MainWindowCore._on_tiktok_error(window, tiktok_offline)

    assert settings.values[MainWindowCore.SETTING_YOUTUBE_OFFLINE] is True
    assert settings.values[MainWindowCore.SETTING_TIKTOK_OFFLINE] is True
    assert window.toast.show_toast.call_count == 2


def test_manual_connect_clears_offline_suppression(qapp, monkeypatch):
    import backend.workers

    monkeypatch.setattr(backend.workers, "YouTubeChatWorker", _ChatWorker)
    monkeypatch.setattr(backend.workers, "TikTokChatWorker", _ChatWorker)
    i18n = TranslationService(default_lang="es")
    settings = _SettingsStorage({
        MainWindowCore.SETTING_YOUTUBE_OFFLINE: True,
        MainWindowCore.SETTING_TIKTOK_OFFLINE: True,
    })
    window = _window(settings, i18n)
    window.dashboard_controller = None
    window._on_youtube_connected = Mock()
    window._on_youtube_disconnected = Mock()
    window._on_youtube_error = Mock()
    window._route_incoming_message = Mock()
    window._on_tiktok_connected = Mock()
    window._on_tiktok_disconnected = Mock()
    window._on_tiktok_error = Mock()

    MainWindowCore._handle_youtube_connect(window, "youtube-channel")
    MainWindowCore._handle_tiktok_connect(window, "@tiktok-channel")

    assert settings.values[MainWindowCore.SETTING_YOUTUBE_OFFLINE] is False
    assert settings.values[MainWindowCore.SETTING_TIKTOK_OFFLINE] is False
