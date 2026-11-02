import logging
from unittest.mock import MagicMock

import frontend.window.composition as composition_module
from frontend.window.composition import MainWindowComposition
from frontend.window.platform_connections import PlatformConnectionHandlers
from frontend.window.startup import StartupSequencer
from frontend.window.wiring import MainWindowWiring


def test_composition_builds_services_and_controllers(monkeypatch):
    constructor_names = (
        "AvatarService",
        "ChatService",
        "SettingsService",
        "RewardsService",
        "RewardRedemptionHandler",
        "CommandService",
        "SpamService",
        "TimerService",
        "KickConnection",
        "WorkerSlot",
        "LogService",
        "DashboardController",
        "ChatController",
        "ChatMessageRouter",
        "WidgetsController",
        "MusicController",
        "MediaKeysHandler",
        "RewardsController",
        "CommandsController",
        "SpamController",
        "TimersController",
        "SettingsController",
        "LogsController",
        "ScheduleController",
        "AlertsController",
        "ConnectionHub",
        "IntegrationsStatusPresenter",
    )
    constructors = {}
    for name in constructor_names:
        constructor = MagicMock(name=name)
        constructors[name] = constructor
        monkeypatch.setattr(composition_module, name, constructor)

    window = MagicMock()
    composition = MainWindowComposition(window)

    composition.create_services()
    composition.create_controllers()

    for name in constructor_names:
        if name == "WorkerSlot":
            assert constructors[name].call_count == 2
            continue
        constructors[name].assert_called_once()

    assert window.chat_service is constructors["ChatService"].return_value
    assert window.kick is constructors["KickConnection"].return_value
    assert window.chat_controller is constructors["ChatController"].return_value
    assert window.connection_hub is constructors["ConnectionHub"].return_value
    assert window.integrations_status is constructors["IntegrationsStatusPresenter"].return_value
    assert isinstance(window.platform_connections, PlatformConnectionHandlers)


def test_wiring_connects_platform_and_application_signals():
    window = MagicMock()

    MainWindowWiring(window).connect_signals()

    window.dashboard_controller.request_connection.connect.assert_called_once_with(
        window.platform_connections.handle_auth_process
    )
    window.kick.connected.connect.assert_called_once_with(
        window.platform_connections.on_kick_connected
    )
    window.twitch.connected.connect.assert_called_once_with(
        window.platform_connections.on_twitch_connected
    )
    window.youtube.error_reported.connect.assert_called_once_with(
        window.platform_connections.on_live_chat_error
    )
    window.tiktok.error_reported.connect.assert_called_once_with(
        window.platform_connections.on_live_chat_error
    )
    window.q_log_handler.emitter.log_received.connect.assert_called_once_with(
        window.logs_controller.process_incoming_log
    )


def test_kick_connection_handler_preserves_startup_toast_suppression():
    window = MagicMock()
    handler = PlatformConnectionHandlers(window)
    window._consume_startup_silent_connection.return_value = True

    handler.on_kick_connected("streamer", {"broadcaster_id": 123})

    window.toast.show_toast.assert_not_called()
    window.kick.fetch_rewards.assert_called_once()


def test_kick_connection_handler_shows_toast_for_manual_connection():
    window = MagicMock()
    handler = PlatformConnectionHandlers(window)
    window._consume_startup_silent_connection.return_value = False

    handler.on_kick_connected("streamer", {"broadcaster_id": 123})

    window.toast.show_toast.assert_called_once()


def test_startup_sequencer_runs_steps_in_order_and_continues_after_failure(caplog):
    scheduled = []
    events = []
    logger = logging.getLogger("test.startup_sequencer")

    def schedule(delay, callback):
        scheduled.append((delay, callback))

    def fail():
        events.append("failed")
        raise RuntimeError("expected test failure")

    sequencer = StartupSequencer(
        logger=logger,
        is_active=lambda: True,
        whats_new_check=lambda: events.append("whats_new"),
        prewarm_views=lambda delay: events.append(("prewarm", delay)),
        start_database_maintenance=lambda: events.append("maintenance"),
        schedule=schedule,
    )

    with caplog.at_level(logging.ERROR, logger="test.startup_sequencer"):
        sequencer.start((("first", lambda: events.append("first")), ("failure", fail), ("last", lambda: events.append("last"))))
        initial_delay, initial_callback = scheduled.pop(0)
        assert initial_delay == StartupSequencer.INITIAL_HYDRATION_DELAY_MS
        initial_callback()

        while scheduled:
            _delay, callback = scheduled.pop(0)
            callback()

    assert events[:4] == ["first", "failed", "last", ("prewarm", StartupSequencer.PREWARM_DELAY_MS)]
    assert events[4:] == ["whats_new", "maintenance"]
    assert len(caplog.records) == 1
    assert "Hydration phase 'failure' failed." in caplog.records[0].getMessage()
