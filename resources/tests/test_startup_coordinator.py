"""Pruebas de la coordinación del arranque de la ventana."""

from unittest.mock import MagicMock

from PySide6.QtCore import QObject, QTimer, Signal

from bootstrap.application import Application
from frontend.window.startup_coordinator import MainWindowStartup, StartupSequencer


class ManualScheduler:
    def __init__(self):
        self.pending = []

    def __call__(self, delay_ms, callback):
        self.pending.append((delay_ms, callback))

    def run(self, delay_ms):
        index = next(
            index
            for index, (scheduled_delay, _callback) in enumerate(self.pending)
            if scheduled_delay == delay_ms
        )
        _scheduled_delay, callback = self.pending.pop(index)
        callback()


def test_autostart_dispatch_waits_for_configured_staggered_requests():
    scheduler = ManualScheduler()
    dispatched = []
    window = MagicMock()
    window._is_shutting_down = False
    window._startup_silent_connections = set()
    window.kick_auth_manager.is_authenticated.return_value = True
    window.container.twitch_token_storage.load.return_value = {"access_token": "saved"}
    window.settings_service.get_font_size.return_value = 12
    window.youtube.saved_target.return_value = "yt-channel"
    window.youtube.is_offline_saved.return_value = False
    window.youtube.platform_id = "youtube"
    window.tiktok.saved_target.return_value = "tt-channel"
    window.tiktok.is_offline_saved.return_value = True
    window.tiktok.log_tag = "TikTok"

    startup = MainWindowStartup(
        window,
        MagicMock(),
        on_connections_dispatched=lambda: dispatched.append(True),
        schedule=scheduler,
    )

    startup._finish_settings_hydration()

    assert window.platform_connections.handle_auth_process.called
    assert [delay for delay, _callback in scheduler.pending] == [1200, 2400]
    assert dispatched == []

    scheduler.run(1200)
    assert window.twitch.resume_session.called
    assert dispatched == []

    scheduler.run(2400)
    assert window.youtube.connect_channel.call_args.args == ("yt-channel",)
    assert window.youtube.connect_channel.call_args.kwargs == {"manual": False}
    assert not window.tiktok.connect_channel.called
    assert dispatched == [True]


def test_autostart_dispatch_completes_immediately_without_saved_platforms():
    scheduler = ManualScheduler()
    dispatched = []
    window = MagicMock()
    window._is_shutting_down = False
    window.kick_auth_manager.is_authenticated.return_value = False
    window.container.twitch_token_storage.load.return_value = None
    window.settings_service.get_font_size.return_value = 12
    window.youtube.saved_target.return_value = ""
    window.tiktok.saved_target.return_value = ""

    startup = MainWindowStartup(
        window,
        MagicMock(),
        on_connections_dispatched=lambda: dispatched.append(True),
        schedule=scheduler,
    )

    startup._finish_settings_hydration()

    assert scheduler.pending == []
    assert dispatched == [True]


def test_startup_followups_can_be_deferred_until_window_is_shown():
    scheduler = ManualScheduler()
    prewarm = MagicMock()
    sequencer = StartupSequencer(
        logger=MagicMock(),
        is_active=lambda: True,
        whats_new_check=MagicMock(),
        prewarm_views=prewarm,
        start_database_maintenance=MagicMock(),
        schedule=scheduler,
    )
    sequencer.defer_followups()

    sequencer.start((("hydration", lambda: None),))
    scheduler.run(50)

    assert scheduler.pending == []
    assert not prewarm.called

    sequencer.resume_followups()

    assert [delay for delay, _callback in scheduler.pending] == [750, 10_000]
    prewarm.assert_called_once_with(8_000)


def test_bootstrap_waits_for_startup_requests_to_be_dispatched(qapp):
    class StartupSignalWindow(QObject):
        startup_connections_dispatched = Signal()

    window = StartupSignalWindow()
    QTimer.singleShot(0, window.startup_connections_dispatched.emit)

    Application()._wait_for_startup_connections(window)
