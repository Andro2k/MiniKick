# resources\tests\test_twitch_connection.py

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, Signal

from backend.connections import TwitchConnection


class _Worker(QObject):
    finished = Signal()
    instances = []

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.started = False
        type(self).instances.append(self)

    def start(self):
        self.started = True

    def isRunning(self):
        return self.started


class _AuthWorker(_Worker):
    auth_success = Signal(object)
    auth_error = Signal(str)
    instances = []


class _ChatWorker(_Worker):
    message_received = Signal(object)
    error_occurred = Signal(str)
    connection_success = Signal(object)
    connection_lost = Signal()
    connection_restored = Signal()
    instances = []


class _RewardWorker(_Worker):
    reward_redeemed = Signal(str, str, str)
    alert_received = Signal(object)
    instances = []


class _FetchWorker(_Worker):
    rewards_fetched = Signal(object, object)
    instances = []


class _ApiClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture(autouse=True)
def _fake_backend(monkeypatch):
    import backend.providers
    import backend.workers

    for worker_class in (_AuthWorker, _ChatWorker, _RewardWorker, _FetchWorker):
        worker_class.instances = []
    monkeypatch.setattr(backend.workers, "TwitchAuthWorker", _AuthWorker)
    monkeypatch.setattr(backend.workers, "TwitchChatWorker", _ChatWorker)
    monkeypatch.setattr(backend.workers, "TwitchRewardWorker", _RewardWorker)
    monkeypatch.setattr(backend.workers, "FetchRewardsWorker", _FetchWorker)
    monkeypatch.setattr(backend.providers, "TwitchAPIClient", _ApiClient)


class _Coordinator:
    def __init__(self, defer=False):
        self.defer = defer
        self.calls = []
        self.pending = []

    def stop_workers(self, workers, on_finished=None, warning_after_seconds=0):
        self.calls.append(list(workers))
        if on_finished is None:
            return
        if self.defer:
            self.pending.append(on_finished)
        else:
            on_finished()


def _auth_manager(authenticated=False, missing_scopes=False):
    return SimpleNamespace(
        is_authenticated=lambda: authenticated,
        has_missing_scopes=lambda: missing_scopes,
        logout=MagicMock(),
    )


def _connection(*, authenticated=False, missing_scopes=False, defer=False, shutting_down=False):
    coordinator = _Coordinator(defer=defer)
    auth_manager = _auth_manager(authenticated, missing_scopes)
    connection = TwitchConnection(
        auth_manager=auth_manager,
        client_id="client-id",
        i18n=MagicMock(),
        coordinator=coordinator,
        is_shutting_down=lambda: shutting_down,
    )
    return connection, coordinator, auth_manager


def _spy(signal):
    events = []
    signal.connect(lambda *args: events.append(args))
    return events


def test_authenticate_stops_workers_then_opens_the_browser_flow(qapp):
    connection, coordinator, _auth = _connection()
    browser = _spy(connection.browser_auth_opening)

    connection.authenticate()

    assert len(coordinator.calls) == 1
    assert [name for name, _worker in coordinator.calls[0]] == [
        "Worker_Twitch_Auth",
        "Worker_Twitch_Chat_Socket",
        "Worker_Twitch_Reward_EventSub",
        "Worker_Fetch_Twitch_Rewards",
    ]
    assert browser == [()]
    assert _AuthWorker.instances[0].started is True
    assert _AuthWorker.instances[0].kwargs == {"force": False}


def test_authenticate_forces_when_scopes_are_missing(qapp):
    connection, _coordinator, _auth = _connection(authenticated=True, missing_scopes=True)
    browser = _spy(connection.browser_auth_opening)

    connection.authenticate()

    assert _AuthWorker.instances[0].kwargs == {"force": True}
    assert browser == [()]


def test_authenticate_with_valid_session_skips_the_browser(qapp):
    connection, _coordinator, _auth = _connection(authenticated=True)
    browser = _spy(connection.browser_auth_opening)

    connection.authenticate()

    assert browser == []
    assert _AuthWorker.instances[0].started is True
    assert connection.is_auth_running is True


def test_authenticate_is_ignored_while_pending_or_shutting_down(qapp):
    pending, coordinator, _auth = _connection(defer=True)
    pending.authenticate()
    pending.authenticate()
    assert len(coordinator.calls) == 1

    closing, closing_coordinator, _auth = _connection(shutting_down=True)
    closing.authenticate()
    assert closing_coordinator.calls == []


def test_auth_success_builds_the_api_and_starts_the_chat_worker(qapp):
    connection, _coordinator, _auth = _connection()
    order = []
    connection.api_changed.connect(lambda api: order.append(("api", api)))
    connection.chat_worker_changed.connect(lambda worker: order.append(("chat", worker)))
    connection.session_started.connect(lambda: order.append(("session", None)))

    connection.resume_session()

    chat_worker = _ChatWorker.instances[0]
    assert connection.api.kwargs["client_id"] == "client-id"
    assert chat_worker.kwargs["api_client"] is connection.api
    assert chat_worker.started is True
    assert [kind for kind, _value in order] == ["api", "chat", "session"]
    assert order[1][1] is chat_worker


def test_auth_error_resets_state_and_reports_the_failure(qapp):
    connection, _coordinator, _auth = _connection()
    states = _spy(connection.state_changed)
    failures = _spy(connection.auth_failed)

    connection.authenticate()
    _AuthWorker.instances[0].auth_error.emit("denied")

    assert connection.is_connected is False
    assert connection.channel == ""
    assert states == [()]
    assert failures == [("denied",)]


def test_chat_connected_publishes_profile_and_starts_reward_workers(qapp):
    connection, _coordinator, _auth = _connection(authenticated=True)
    connected = _spy(connection.connected)

    connection.resume_session()
    profile = {"username": "streamer", "broadcaster_id": "42", "avatar_url": "http://img"}
    _ChatWorker.instances[0].connection_success.emit(profile)

    assert connected == [("streamer", "42", profile)]
    assert connection.is_connected is True
    assert connection.channel == "streamer"
    assert connection.broadcaster_id == "42"
    assert connection.avatar_url == "http://img"
    assert _RewardWorker.instances[0].args[-1] == "42"
    assert _RewardWorker.instances[0].started is True
    assert _FetchWorker.instances[0].kwargs == {"broadcaster_id": "42", "platform": "twitch"}


def test_chat_connected_without_authentication_does_not_start_reward_workers(qapp):
    connection, _coordinator, _auth = _connection(authenticated=False)

    connection.resume_session()
    _ChatWorker.instances[0].connection_success.emit({"username": "streamer", "broadcaster_id": "42"})

    assert _RewardWorker.instances == []
    assert _FetchWorker.instances == []


def test_chat_connected_keeps_known_identity_for_partial_payloads(qapp):
    connection, _coordinator, _auth = _connection()
    connected = _spy(connection.connected)

    connection.resume_session()
    worker = _ChatWorker.instances[0]
    worker.connection_success.emit({"username": "streamer", "broadcaster_id": "42"})
    worker.connection_success.emit("renamed")
    worker.connection_success.emit(None)

    assert connected[1] == ("renamed", "42", {})
    assert connected[2] == ("renamed", "42", {})
    assert connection.channel == "renamed"
    assert connection.broadcaster_id == "42"


def test_chat_error_stops_the_worker_and_reports(qapp):
    connection, coordinator, _auth = _connection()
    workers = []
    connection.chat_worker_changed.connect(workers.append)
    states = _spy(connection.state_changed)
    errors = _spy(connection.error_reported)

    connection.resume_session()
    _ChatWorker.instances[0].connection_success.emit({"username": "streamer"})
    _ChatWorker.instances[0].error_occurred.emit("socket closed")

    assert connection.is_connected is False
    assert workers[-1] is None
    assert states == [(), (), ()]
    assert errors == [("socket closed",)]
    assert coordinator.calls[-1][0][0] == "Worker_Twitch_Chat_Socket"


def test_socket_loss_and_restore_toggle_the_connected_state(qapp):
    connection, _coordinator, _auth = _connection()
    states = _spy(connection.state_changed)

    connection.resume_session()
    worker = _ChatWorker.instances[0]
    worker.connection_lost.emit()
    assert connection.is_connected is False
    worker.connection_restored.emit()
    assert connection.is_connected is True
    assert len(states) == 3


def test_disconnect_logs_out_and_clears_the_session(qapp):
    connection, coordinator, auth_manager = _connection()
    events = []
    connection.api_changed.connect(lambda api: events.append(("api", api)))
    connection.chat_worker_changed.connect(lambda worker: events.append(("chat", worker)))
    connection.disconnected.connect(lambda: events.append(("disconnected", None)))

    connection.resume_session()
    _ChatWorker.instances[0].connection_success.emit({"username": "streamer", "broadcaster_id": "42"})
    events.clear()
    connection.disconnect_account()

    auth_manager.logout.assert_called_once_with()
    assert connection.api is None
    assert connection.broadcaster_id == ""
    assert connection.is_connected is False
    assert connection.channel == ""
    assert events == [("api", None), ("chat", None), ("disconnected", None)]
    assert len(coordinator.calls[-1]) == 4


def test_disconnect_is_ignored_while_authentication_is_starting(qapp):
    connection, coordinator, auth_manager = _connection(defer=True)

    connection.authenticate()
    connection.disconnect_account()

    assert len(coordinator.calls) == 1
    auth_manager.logout.assert_not_called()


def test_worker_signals_are_forwarded(qapp):
    connection, _coordinator, _auth = _connection(authenticated=True)
    messages = _spy(connection.message_received)
    redeemed = _spy(connection.reward_redeemed)
    alerts = _spy(connection.alert_received)
    fetched = _spy(connection.rewards_fetched)

    connection.resume_session()
    _ChatWorker.instances[0].connection_success.emit({"username": "s", "broadcaster_id": "42"})
    _ChatWorker.instances[0].message_received.emit("dto")
    _RewardWorker.instances[0].reward_redeemed.emit("viewer", "Hydrate", "msg")
    _RewardWorker.instances[0].alert_received.emit("alert")
    _FetchWorker.instances[0].rewards_fetched.emit([1], [2])

    assert messages == [("dto",)]
    assert redeemed == [("viewer", "Hydrate", "msg")]
    assert alerts == [("alert",)]
    assert fetched == [([1], [2])]


def test_fetch_rewards_requires_authentication_and_skips_when_busy(qapp):
    anonymous, _coordinator, _auth = _connection(authenticated=False)
    anonymous.fetch_rewards("42")
    assert _FetchWorker.instances == []

    connection, _coordinator, _auth = _connection(authenticated=True)
    connection.fetch_rewards("42")
    connection.fetch_rewards("42")

    assert len(_FetchWorker.instances) == 1
    assert connection.api is None
    assert _FetchWorker.instances[0].args[0].kwargs["client_id"] == "client-id"


def test_failed_session_start_publishes_the_disconnected_state(qapp, monkeypatch):
    connection, _coordinator, _auth = _connection(authenticated=True)
    connection._is_connected = True
    connection._channel = "streamer"
    monkeypatch.setattr(connection, "_build_api", MagicMock(side_effect=RuntimeError("boom")))
    seen = []
    failures = _spy(connection.auth_failed)
    connection.state_changed.connect(lambda: seen.append((connection.is_connected, connection.channel)))

    connection.resume_session()

    assert seen[-1] == (False, "")
    assert failures == [("boom",)]
