# backend\connections\twitch.py

import logging
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal

from .worker_shutdown import WorkerShutdownCoordinator
from .worker_slot import WorkerSlot

logger = logging.getLogger("minikick.core")

_STOP_WARNING_SECONDS = 10.0


class TwitchConnection(QObject):
    state_changed = Signal()
    message_received = Signal(object)
    browser_auth_opening = Signal()
    auth_failed = Signal(str)
    session_started = Signal()
    api_changed = Signal(object)
    chat_worker_changed = Signal(object)
    connected = Signal(str, str, object)
    disconnected = Signal()
    error_reported = Signal(str)
    reward_redeemed = Signal(str, str, str)
    alert_received = Signal(object)
    rewards_fetched = Signal(object, object)

    def __init__(
        self,
        auth_manager,
        client_id: str,
        i18n,
        coordinator: WorkerShutdownCoordinator,
        is_shutting_down: Callable[[], bool],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._auth_manager = auth_manager
        self._client_id = client_id
        self._i18n = i18n
        self._coordinator = coordinator
        self._is_shutting_down = is_shutting_down
        self._auth_slot = WorkerSlot("Worker_Twitch_Auth", coordinator)
        self._chat_slot = WorkerSlot("Worker_Twitch_Chat_Socket", coordinator)
        self._reward_slot = WorkerSlot("Worker_Twitch_Reward_EventSub", coordinator)
        self._fetch_slot = WorkerSlot("Worker_Fetch_Twitch_Rewards", coordinator)
        self.slots = (self._auth_slot, self._chat_slot, self._reward_slot, self._fetch_slot)
        self.api = None
        self.broadcaster_id = ""
        self.avatar_url = ""
        self._is_connected = False
        self._channel = ""
        self._auth_start_pending = False
        self._disconnect_pending = False
        self._chat_start_pending = False
        self._reward_start_pending = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def is_auth_running(self) -> bool:
        return self._auth_slot.is_running

    def authenticate(self, *, force: bool = False) -> None:
        if self._auth_start_pending or self._disconnect_pending or self._is_shutting_down():
            return
        self._auth_start_pending = True
        self._stop_workers(on_finished=lambda: self._start_auth_worker(force))

    def resume_session(self) -> None:
        self._on_auth_success(None)

    def disconnect_account(self) -> None:
        if self._disconnect_pending or self._auth_start_pending:
            return
        self._disconnect_pending = True
        logger.info("[User Action] Twitch account unlinked successfully")
        self._stop_workers(on_finished=self._finish_disconnect)

    def fetch_rewards(self, broadcaster_id: str = "") -> None:
        target_id = broadcaster_id or self.broadcaster_id
        if not self._auth_manager.is_authenticated():
            return
        if self._fetch_slot.is_running:
            return
        try:
            api = self.api or self._build_api()
            self._fetch_slot.start(lambda: self._build_fetch_worker(api, target_id))
        except Exception:
            logger.exception("[Main] Error launching Twitch rewards fetcher.")

    def _build_api(self):
        from backend.providers import TwitchAPIClient

        return TwitchAPIClient(
            auth_provider=self._auth_manager,
            client_id=self._client_id,
            i18n=self._i18n,
        )

    def _stop_workers(self, on_finished: Callable[[], None] | None = None) -> None:
        self._coordinator.stop_workers(
            [slot.detach() for slot in self.slots],
            on_finished=on_finished,
            warning_after_seconds=_STOP_WARNING_SECONDS,
        )

    def _start_auth_worker(self, force: bool) -> None:
        self._auth_start_pending = False
        if self._is_shutting_down():
            return
        if not force and self._auth_manager.has_missing_scopes():
            force = True
        if force or not self._auth_manager.is_authenticated():
            self.browser_auth_opening.emit()
        self._auth_slot.start(lambda: self._build_auth_worker(force))

    def _build_auth_worker(self, force: bool) -> QThread:
        from backend.workers import TwitchAuthWorker

        worker = TwitchAuthWorker(self._auth_manager, force=force)
        worker.auth_success.connect(self._on_auth_success)
        worker.auth_error.connect(self._on_auth_error)
        worker.finished.connect(lambda: self._auth_slot.forget(worker))
        worker.finished.connect(worker.deleteLater)
        return worker

    def _on_auth_error(self, error: str) -> None:
        self._auth_slot.detach()
        self._is_connected = False
        self._channel = ""
        self.state_changed.emit()
        logger.error("[TwitchAuth] Authentication error: %s", error)
        self.auth_failed.emit(error)

    def _on_auth_success(self, _tokens) -> None:
        self._auth_slot.detach()
        logger.info("[Twitch Auth] Success callback received.")
        self.state_changed.emit()
        try:
            self.api = self._build_api()
            self.api_changed.emit(self.api)
            self._start_chat_worker("")
            self.session_started.emit()
        except Exception as error:
            logger.exception("[Twitch Auth] Error initializing Twitch session.")
            self._is_connected = False
            self._channel = ""
            self.auth_failed.emit(str(error))

    def _start_chat_worker(self, channel: str) -> None:
        if self._chat_start_pending or self._is_shutting_down():
            return
        self._chat_start_pending = True
        self._chat_slot.stop(on_finished=lambda: self._create_chat_worker(channel))

    def _create_chat_worker(self, channel: str) -> None:
        self._chat_start_pending = False
        if self._is_shutting_down():
            return
        self._chat_slot.start(lambda: self._build_chat_worker(channel))

    def _build_chat_worker(self, channel: str) -> QThread:
        from backend.workers import TwitchChatWorker

        worker = TwitchChatWorker(
            channel_name=channel,
            oauth_token="",
            bot_nick="",
            api_client=self.api,
            i18n=self._i18n,
        )
        self.chat_worker_changed.emit(worker)
        worker.connection_success.connect(self._on_chat_connected)
        worker.connection_lost.connect(self._on_socket_lost)
        worker.connection_restored.connect(self._on_socket_restored)
        worker.error_occurred.connect(self._on_chat_error)
        worker.message_received.connect(self.message_received)
        return worker

    def _on_chat_error(self, error_msg: str) -> None:
        self._is_connected = False
        self._chat_slot.stop()
        self.chat_worker_changed.emit(None)
        self.state_changed.emit()
        self.error_reported.emit(error_msg)

    def _on_chat_connected(self, user_data=None) -> None:
        profile = {}
        if isinstance(user_data, dict):
            username = user_data.get("username", "")
            broadcaster_id = user_data.get("broadcaster_id", "")
            self.avatar_url = user_data.get("avatar_url", "")
            profile = user_data
        elif isinstance(user_data, str):
            username = user_data
            broadcaster_id = self.broadcaster_id
        else:
            username = self._channel
            broadcaster_id = self.broadcaster_id

        if broadcaster_id:
            self.broadcaster_id = broadcaster_id
        self._is_connected = True
        if username:
            self._channel = username
        self.state_changed.emit()
        self.connected.emit(username, broadcaster_id, profile)

        if broadcaster_id and self._auth_manager.is_authenticated():
            self._start_reward_worker(broadcaster_id)
            self.fetch_rewards(broadcaster_id)

    def _on_socket_lost(self) -> None:
        self._is_connected = False
        logger.warning("[Twitch] Connection lost for channel '%s'.", self._channel or "?")
        self.state_changed.emit()

    def _on_socket_restored(self) -> None:
        self._is_connected = True
        logger.info("[Twitch] Connection restored for channel '%s'.", self._channel or "?")
        self.state_changed.emit()

    def _start_reward_worker(self, broadcaster_id: str) -> None:
        if self._reward_start_pending or self._is_shutting_down():
            return
        self._reward_start_pending = True
        self._reward_slot.stop(on_finished=lambda: self._create_reward_worker(broadcaster_id))

    def _create_reward_worker(self, broadcaster_id: str) -> None:
        self._reward_start_pending = False
        if self._is_shutting_down():
            return
        self._reward_slot.start(lambda: self._build_reward_worker(broadcaster_id))

    def _build_reward_worker(self, broadcaster_id: str) -> QThread:
        from backend.workers import TwitchRewardWorker

        worker = TwitchRewardWorker(
            self._i18n,
            self._auth_manager,
            self._client_id,
            broadcaster_id,
        )
        worker.reward_redeemed.connect(self.reward_redeemed)
        worker.alert_received.connect(self.alert_received)
        return worker

    def _build_fetch_worker(self, api, broadcaster_id: str) -> QThread:
        from backend.workers import FetchRewardsWorker

        worker = FetchRewardsWorker(api, broadcaster_id=broadcaster_id, platform="twitch")
        worker.rewards_fetched.connect(self.rewards_fetched)
        worker.finished.connect(lambda: self._fetch_slot.forget(worker))
        worker.finished.connect(worker.deleteLater)
        return worker

    def _finish_disconnect(self) -> None:
        self._disconnect_pending = False
        if self._is_shutting_down():
            return
        self.api = None
        self.broadcaster_id = ""
        self.api_changed.emit(None)
        self.chat_worker_changed.emit(None)
        self._auth_manager.logout()
        self._is_connected = False
        self._channel = ""
        self.state_changed.emit()
        self.disconnected.emit()
