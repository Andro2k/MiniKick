# resources\tests\test_kick_connection.py

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, Signal

from backend.connections import KickConnection


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
    poll_updated = Signal(object)
    poll_deleted = Signal()
    pinned_created = Signal(object)
    pinned_deleted = Signal()
    reward_redeemed = Signal(str, str, str)
    goal_progress = Signal(object)
    instances = []


class _TimerWorker(_Worker):
    post_message_requested = Signal(str, bool, bool)
    instances = []


class _FetchWorker(_Worker):
    rewards_fetched = Signal(object, object)
    error_occurred = Signal(str)
    instances = []


class _ApiClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture(autouse=True)
def _fake_backend(monkeypatch):
    import backend.providers
    import backend.workers

    for worker_class in (_AuthWorker, _ChatWorker, _TimerWorker, _FetchWorker):
        worker_class.instances = []
    monkeypatch.setattr(backend.workers, "KickAuthWorker", _AuthWorker)
    monkeypatch.setattr(backend.workers, "KickChatWorker", _ChatWorker)
    monkeypatch.setattr(backend.workers, "TimerWorker", _TimerWorker)
    monkeypatch.setattr(backend.workers, "FetchRewardsWorker", _FetchWorker)
    monkeypatch.setattr(backend.providers, "KickAPIClient", _ApiClient)


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


def _connection(*, authenticated=True, defer=False, shutting_down=False):
    coordinator = _Coordinator(defer=defer)
    auth_manager = SimpleNamespace(is_authenticated=lambda: authenticated, logout=MagicMock())
    i18n = MagicMock()
    i18n.get.return_value = "setup error: {error}"
    timer_service = object()
    connection = KickConnection(
        auth_manager=auth_manager,
        i18n=i18n,
        timer_service=timer_service,
        pusher=SimpleNamespace(cluster="eu", keys=("key",)),
        coordinator=coordinator,
        is_shutting_down=lambda: shutting_down,
    )
    return connection, coordinator, auth_manager, timer_service


def _spy(signal):
    events = []
    signal.connect(lambda *args: events.append(args))
    return events


def _authenticated_session(connection, user_data=None):
    connection.authenticate()
    _AuthWorker.instances[0].auth_success.emit({})
    _ChatWorker.instances[0].connection_success.emit(
        user_data or {"username": "My_Streamer 1", "broadcaster_id": 7}
    )


def test_authenticate_stops_workers_then_starts_the_auth_worker(qapp):
    connection, coordinator, auth_manager, _timers = _connection()
    connecting = _spy(connection.connecting)

    connection.authenticate(force=True)

    assert [name for name, _worker in coordinator.calls[0]] == [
        "Worker_Kick_Auth",
        "Worker_Kick_Chat_Socket",
        "Worker_Fetch_Rewards",
        "Worker_Timers",
    ]
    assert connecting == [()]
    assert _AuthWorker.instances[0].started is True
    assert _AuthWorker.instances[0].args[1] is auth_manager
    assert _AuthWorker.instances[0].kwargs == {"force": True}
    assert connection.is_auth_running is True


def test_authenticate_is_ignored_while_pending_disconnecting_or_closing(qapp):
    pending, coordinator, _auth, _timers = _connection(defer=True)
    pending.authenticate()
    pending.authenticate()
    assert len(coordinator.calls) == 1

    disconnecting, disconnect_coordinator, _auth, _timers = _connection(defer=True)
    disconnecting.disconnect_account()
    disconnecting.authenticate()
    assert len(disconnect_coordinator.calls) == 1

    closing, closing_coordinator, _auth, _timers = _connection(shutting_down=True)
    closing.authenticate()
    assert closing_coordinator.calls == []


def test_auth_success_publishes_the_api_and_starts_the_chat_worker(qapp):
    connection, _coordinator, auth_manager, _timers = _connection()
    published = _spy(connection.api_changed)

    connection.authenticate()
    _AuthWorker.instances[0].auth_success.emit({})

    chat = _ChatWorker.instances[0]
    assert connection.api.kwargs == {"auth_provider": auth_manager}
    assert published == [(connection.api,)]
    assert chat.args[1] is connection.api
    assert chat.args[2:] == ("eu", ("key",))
    assert chat.started is True
    assert connection.is_auth_running is False


def test_chat_connected_publishes_identity_and_starts_the_timers_worker(qapp):
    connection, _coordinator, _auth, timer_service = _connection()
    connected = _spy(connection.connected)
    user_data = {"username": "My_Streamer 1", "broadcaster_id": 7, "profile_pic": "pic"}

    _authenticated_session(connection, user_data)

    assert connected == [("My_Streamer 1", user_data)]
    assert connection.is_connected is True
    assert connection.username == "My_Streamer 1"
    assert connection.avatar_url == "pic"
    timers = _TimerWorker.instances[0]
    assert timers.args[0] is timer_service
    assert timers.args[2] == "My-Streamer1"
    assert timers.started is True


def test_timers_worker_is_not_started_for_a_stale_generation(qapp):
    connection, coordinator, _auth, _timers = _connection(defer=True)

    connection._on_chat_connected({"username": "first"})
    connection._on_chat_connected({"username": "second"})
    for callback in coordinator.pending:
        callback()

    assert [worker.args[2] for worker in _TimerWorker.instances] == ["second"]


def test_disconnect_logs_out_and_clears_identity_once(qapp):
    connection, _coordinator, auth_manager, _timers = _connection()
    disconnected = _spy(connection.disconnected)
    _authenticated_session(connection)

    assert connection.disconnect_account() is True

    auth_manager.logout.assert_called_once_with()
    assert connection.is_connected is False
    assert connection.username == ""
    assert disconnected == [()]


def test_disconnect_reports_when_one_is_already_pending(qapp):
    connection, _coordinator, _auth, _timers = _connection(defer=True)

    assert connection.disconnect_account() is True
    assert connection.disconnect_account() is False


def test_reauthenticate_clears_the_session_and_signals_readiness(qapp):
    connection, _coordinator, auth_manager, _timers = _connection()
    ready = _spy(connection.reauth_ready)
    _authenticated_session(connection)

    connection.reauthenticate()

    auth_manager.logout.assert_called_once_with()
    assert connection.is_connected is False
    assert ready == [()]


def test_reauthenticate_ignores_repeated_requests_and_shutdown(qapp):
    pending, coordinator, _auth, _timers = _connection(defer=True)
    pending.reauthenticate()
    pending.reauthenticate()
    assert len(coordinator.calls) == 1

    closing, closing_coordinator, _auth, _timers = _connection(shutting_down=True)
    closing.reauthenticate()
    assert closing_coordinator.calls == []


def test_chat_worker_signals_are_forwarded(qapp):
    connection, _coordinator, _auth, _timers = _connection()
    forwarded = {
        "message": _spy(connection.message_received),
        "poll": _spy(connection.poll_updated),
        "poll_deleted": _spy(connection.poll_deleted),
        "pinned": _spy(connection.pinned_created),
        "pinned_deleted": _spy(connection.pinned_deleted),
        "reward": _spy(connection.reward_redeemed),
        "goal": _spy(connection.goal_progress),
        "error": _spy(connection.error_reported),
    }

    _authenticated_session(connection)
    chat = _ChatWorker.instances[0]
    chat.message_received.emit("dto")
    chat.poll_updated.emit({"p": 1})
    chat.poll_deleted.emit()
    chat.pinned_created.emit({"m": 1})
    chat.pinned_deleted.emit()
    chat.reward_redeemed.emit("viewer", "Hydrate", "hi")
    chat.goal_progress.emit({"goal_type": "followers"})
    chat.error_occurred.emit("socket error")

    assert forwarded["message"] == [("dto",)]
    assert forwarded["poll"] == [({"p": 1},)]
    assert forwarded["poll_deleted"] == [()]
    assert forwarded["pinned"] == [({"m": 1},)]
    assert forwarded["pinned_deleted"] == [()]
    assert forwarded["reward"] == [("viewer", "Hydrate", "hi")]
    assert forwarded["goal"] == [({"goal_type": "followers"},)]
    assert forwarded["error"] == [("socket error",)]


def test_auth_errors_are_reported_and_timer_messages_forwarded(qapp):
    connection, _coordinator, _auth, _timers = _connection()
    errors = _spy(connection.error_reported)
    timer_messages = _spy(connection.timer_message_requested)

    connection.authenticate()
    _AuthWorker.instances[0].auth_error.emit("denied")
    _authenticated_session(connection)
    _TimerWorker.instances[0].post_message_requested.emit("hello", True, False)

    assert errors == [("denied",)]
    assert timer_messages == [("hello", True, False)]


def test_fetch_rewards_requires_authentication_and_skips_when_busy(qapp):
    anonymous, _coordinator, _auth, _timers = _connection(authenticated=False)
    anonymous.fetch_rewards()
    assert _FetchWorker.instances == []

    connection, _coordinator, _auth, _timers = _connection()
    fetched = _spy(connection.rewards_fetched)
    failures = _spy(connection.rewards_error)
    connection.fetch_rewards()
    connection.fetch_rewards()
    worker = _FetchWorker.instances[0]
    worker.rewards_fetched.emit([1], [2])
    worker.error_occurred.emit("api down")

    assert len(_FetchWorker.instances) == 1
    assert worker.kwargs == {"platform": "kick"}
    assert fetched == [([1], [2])]
    assert failures == [("api down",)]


def test_fetch_rewards_survives_a_worker_setup_failure(qapp, monkeypatch):
    import backend.workers

    monkeypatch.setattr(backend.workers, "FetchRewardsWorker", MagicMock(side_effect=RuntimeError("boom")))
    connection, _coordinator, _auth, _timers = _connection()

    connection.fetch_rewards()

    assert connection.is_connected is False
