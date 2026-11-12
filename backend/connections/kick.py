# backend\connections\kick.py

import logging
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal

from .worker_shutdown import WorkerShutdownCoordinator
from .worker_slot import WorkerSlot

logger = logging.getLogger("minikick.core")

_STOP_WARNING_SECONDS = 10.0


class KickConnection(QObject):
    state_changed = Signal()
    connecting = Signal()
    error_reported = Signal(str)
    api_changed = Signal(object)
    connected = Signal(str, object)
    disconnected = Signal()
    reauth_ready = Signal()
    message_received = Signal(object)
    poll_updated = Signal(object)
    poll_deleted = Signal()
    pinned_created = Signal(object)
    pinned_deleted = Signal()
    reward_redeemed = Signal(str, str, str)
    goal_progress = Signal(object)
    rewards_fetched = Signal(object, object)
    rewards_error = Signal(str)
    timer_message_requested = Signal(str, bool, bool)

    def __init__(
        self,
        auth_manager,
        i18n,
        timer_service,
        pusher,
        coordinator: WorkerShutdownCoordinator,
        is_shutting_down: Callable[[], bool],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._auth_manager = auth_manager
        self._i18n = i18n
        self._timer_service = timer_service
        self._pusher = pusher
        self._coordinator = coordinator
        self._is_shutting_down = is_shutting_down
        self._auth_slot = WorkerSlot("Worker_Kick_Auth", coordinator)
        self._chat_slot = WorkerSlot("Worker_Kick_Chat_Socket", coordinator)
        self._fetch_slot = WorkerSlot("Worker_Fetch_Rewards", coordinator)
        self._timers_slot = WorkerSlot("Worker_Timers", coordinator)
        self.slots = (self._auth_slot, self._chat_slot, self._fetch_slot, self._timers_slot)
        self.api = None
        self.username = ""
        self.avatar_url = ""
        self._is_connected = False
        self._auth_start_pending = False
        self._reauth_pending = False
        self._disconnect_pending = False
        self._timers_generation = 0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_auth_running(self) -> bool:
        return self._auth_slot.is_running

    @property
    def channel(self) -> str:
        return self.username

    def authenticate(self, *, force: bool = False) -> None:
        if self._auth_start_pending or self._disconnect_pending or self._is_shutting_down():
            return
        self._auth_start_pending = True
        self._stop_workers(on_finished=lambda: self._start_auth_worker(force))

    def reauthenticate(self) -> None:
        if self._reauth_pending or self._is_shutting_down():
            return
        self._reauth_pending = True
        logger.info("[User Action] Requested renewal of Kick permissions")
        self._stop_workers(on_finished=self._finish_reauth)

    def disconnect_account(self) -> bool:
        if self._disconnect_pending:
            return False
        self._disconnect_pending = True
        logger.info("[User Action] Kick account unlinked successfully")
        self._stop_workers(on_finished=self._finish_disconnect)
        return True

    def fetch_rewards(self) -> None:
        if not self._auth_manager.is_authenticated():
            logger.debug("Kick auth not active, skipping Kick rewards fetch")
            return
        if self._fetch_slot.is_running:
            return
        try:
            self._fetch_slot.start(self._build_fetch_worker)
        except Exception as error:
            logger.exception("Error preparing rewards query: %s", error)

    def _build_api(self):
        from backend.providers import KickAPIClient

        return KickAPIClient(auth_provider=self._auth_manager)

    def _stop_workers(self, on_finished: Callable[[], None] | None = None) -> None:
        self._timers_generation += 1
        self._coordinator.stop_workers(
            [slot.detach() for slot in self.slots],
            on_finished=on_finished,
            warning_after_seconds=_STOP_WARNING_SECONDS,
        )

    def _start_auth_worker(self, force: bool) -> None:
        self._auth_start_pending = False
        if self._is_shutting_down():
            return
        self.connecting.emit()
        self._auth_slot.start(lambda: self._build_auth_worker(force))

    def _build_auth_worker(self, force: bool) -> QThread:
        from backend.workers import KickAuthWorker

        worker = KickAuthWorker(self._i18n, self._auth_manager, force=force)
        worker.auth_success.connect(self._on_auth_success)
        worker.auth_error.connect(self.error_reported)
        worker.finished.connect(lambda: self._auth_slot.forget(worker))
        worker.finished.connect(worker.deleteLater)
        return worker

    def _on_auth_success(self, _tokens) -> None:
        self.state_changed.emit()
        self.api = self._build_api()
        self.api_changed.emit(self.api)
        self._chat_slot.start(self._build_chat_worker)
        self._auth_slot.detach()

    def _build_chat_worker(self) -> QThread:
        from backend.workers import KickChatWorker

        worker = KickChatWorker(self._i18n, self.api, self._pusher.cluster, self._pusher.keys)
        worker.connection_success.connect(self._on_chat_connected)
        worker.message_received.connect(self.message_received)
        worker.poll_updated.connect(self.poll_updated)
        worker.poll_deleted.connect(self.poll_deleted)
        worker.pinned_created.connect(self.pinned_created)
        worker.pinned_deleted.connect(self.pinned_deleted)
        worker.reward_redeemed.connect(self.reward_redeemed)
        worker.goal_progress.connect(self.goal_progress)
        worker.error_occurred.connect(self.error_reported)
        return worker

    def _on_chat_connected(self, user_data: dict) -> None:
        username = user_data.get("username", "Kick")
        self._is_connected = True
        self.username = username
        self.avatar_url = user_data.get("avatar_url") or user_data.get("profile_pic", "")
        self.state_changed.emit()
        self.connected.emit(username, user_data)
        self._start_timers_worker(username.replace("_", "-").replace(" ", ""))

    def _start_timers_worker(self, channel_slug: str) -> None:
        if self._disconnect_pending or self._reauth_pending:
            return
        self._timers_generation += 1
        generation = self._timers_generation
        self._timers_slot.stop(
            on_finished=lambda: self._create_timers_worker(channel_slug, generation),
        )

    def _create_timers_worker(self, channel_slug: str, generation: int) -> None:
        if generation != self._timers_generation or self._is_shutting_down():
            return
        self._timers_slot.start(lambda: self._build_timers_worker(channel_slug))

    def _build_timers_worker(self, channel_slug: str) -> QThread:
        from backend.workers import TimerWorker

        worker = TimerWorker(self._timer_service, self._build_api(), channel_slug)
        worker.post_message_requested.connect(self.timer_message_requested)
        return worker

    def _build_fetch_worker(self) -> QThread:
        from backend.workers import FetchRewardsWorker

        worker = FetchRewardsWorker(self._build_api(), platform="kick")
        worker.rewards_fetched.connect(self.rewards_fetched)
        worker.error_occurred.connect(self.rewards_error)
        worker.finished.connect(lambda: self._fetch_slot.forget(worker))
        worker.finished.connect(worker.deleteLater)
        return worker

    def _reset_identity(self) -> None:
        self._auth_manager.logout()
        self._is_connected = False
        self.username = ""
        self.state_changed.emit()

    def _finish_reauth(self) -> None:
        self._reauth_pending = False
        if self._is_shutting_down():
            return
        self._reset_identity()
        self.reauth_ready.emit()

    def _finish_disconnect(self) -> None:
        self._disconnect_pending = False
        if self._is_shutting_down():
            return
        self._reset_identity()
        self.disconnected.emit()
