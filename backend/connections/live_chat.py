# backend\connections\live_chat.py

import logging
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal

from backend.interfaces import IConfigProvider

from .worker_shutdown import WorkerShutdownCoordinator
from .worker_slot import WorkerSlot

logger = logging.getLogger("minikick.core")


class LiveChatConnection(QObject):
    connecting = Signal()
    connected = Signal(str)
    disconnected = Signal()
    error_reported = Signal(str, bool)
    state_changed = Signal()
    message_received = Signal(object)

    platform_id = ""
    log_tag = ""
    log_name = ""
    thread_name = ""
    target_setting_key = ""
    offline_setting_key = ""
    offline_message_key = ""
    offline_placeholder = ""

    def __init__(
        self,
        config: IConfigProvider,
        i18n,
        coordinator: WorkerShutdownCoordinator,
        is_shutting_down: Callable[[], bool],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._i18n = i18n
        self._is_shutting_down = is_shutting_down
        self.slot = WorkerSlot(self.thread_name, coordinator)
        self._is_connected = False
        self._channel = ""
        self._connect_pending = False
        self._disconnect_pending = False
        self._generation = 0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def channel(self) -> str:
        return self._channel

    def saved_target(self) -> str:
        return self._config.load_string(self.target_setting_key, "")

    def is_offline_saved(self) -> bool:
        return self._config.load_bool(self.offline_setting_key, False)

    def connect_channel(self, target: str, *, manual: bool = True) -> None:
        target = self._normalize_target(target)
        if not target:
            return
        if manual:
            self._config.save_bool(self.offline_setting_key, False)
        if self._connect_pending or self._disconnect_pending or self._is_shutting_down():
            return
        self._connect_pending = True
        generation = self._advance_generation()
        self.connecting.emit()
        self.slot.stop(on_finished=lambda: self._start_worker(target, generation))

    def disconnect_channel(self) -> None:
        if self._disconnect_pending:
            return
        self._disconnect_pending = True
        logger.info("[User Action] %s disconnected successfully", self.log_name)
        self._advance_generation()
        self._connect_pending = False
        self.slot.stop(on_finished=self._finish_disconnect)

    def forget_channel(self) -> None:
        self._config.save_string(self.target_setting_key, "")
        self.disconnect_channel()

    def _normalize_target(self, target: str) -> str:
        return target

    def _create_worker(self, _target: str) -> QThread:
        raise NotImplementedError

    def _describe_stream(self, _stream_info: dict) -> tuple[str, str, str]:
        raise NotImplementedError

    def _advance_generation(self) -> int:
        self._generation += 1
        return self._generation

    def _start_worker(self, target: str, generation: int) -> None:
        if generation != self._generation:
            return
        self._connect_pending = False
        if self._is_shutting_down():
            return
        self.slot.start(lambda: self._build_worker(target))

    def _build_worker(self, target: str) -> QThread:
        worker = self._create_worker(target)
        worker.connection_success.connect(self._on_connected)
        worker.connection_lost.connect(self._on_connection_lost)
        worker.error_occurred.connect(self._on_error)
        worker.message_received.connect(self.message_received.emit)
        return worker

    def _finish_disconnect(self) -> None:
        self._disconnect_pending = False
        if self._is_shutting_down():
            return
        self._is_connected = False
        self._channel = ""
        self._config.save_bool(self.offline_setting_key, False)
        self._config.save_string(self.target_setting_key, "")
        self.state_changed.emit()
        self.disconnected.emit()

    def _on_connected(self, stream_info: dict) -> None:
        display_name, target, log_message = self._describe_stream(stream_info)
        self._is_connected = True
        self._channel = display_name
        self._config.save_bool(self.offline_setting_key, False)
        if target:
            self._config.save_string(self.target_setting_key, target)
        logger.info(log_message)
        self.state_changed.emit()
        self.connected.emit(display_name)

    def _on_connection_lost(self) -> None:
        self._is_connected = False
        self.state_changed.emit()

    def _on_error(self, error_msg: str) -> None:
        self._is_connected = False
        is_offline = self._is_offline_error(error_msg)
        if is_offline:
            self._config.save_bool(self.offline_setting_key, True)
            logger.warning("[%s] %s worker offline status: %s", self.log_tag, self.log_name, error_msg)
        else:
            logger.error("[%s] Error in %s worker: %s", self.log_tag, self.log_name, error_msg)
        self.slot.stop(timeout_ms=1000)
        self.state_changed.emit()
        self.error_reported.emit(error_msg, is_offline)

    def _is_offline_error(self, error_msg: str) -> bool:
        offline_prefix = self._i18n.get(self.offline_message_key).split(self.offline_placeholder, 1)[0]
        return bool(offline_prefix and error_msg.startswith(offline_prefix))


class YouTubeConnection(LiveChatConnection):
    platform_id = "youtube"
    log_tag = "YouTube"
    log_name = "YouTube Live"
    thread_name = "Worker_YouTube_Chat"
    target_setting_key = "youtube_target_channel"
    offline_setting_key = "youtube_stream_offline"
    offline_message_key = "logs.youtube.video_not_found"
    offline_placeholder = "{target}"

    def _create_worker(self, target: str) -> QThread:
        from backend.workers import YouTubeChatWorker

        return YouTubeChatWorker(target_channel=target, i18n=self._i18n)

    def _describe_stream(self, stream_info: dict) -> tuple[str, str, str]:
        channel = stream_info.get("channel", "")
        name = stream_info.get("channel_name", "") or stream_info.get("title", "") or channel or "YouTube Live"
        return name, channel, f"[YouTube] Connected to YouTube Live: '{name}'."


class TikTokConnection(LiveChatConnection):
    platform_id = "tiktok"
    log_tag = "TikTok"
    log_name = "TikTok Live"
    thread_name = "Worker_TikTok_Chat"
    target_setting_key = "tiktok_target_channel"
    offline_setting_key = "tiktok_stream_offline"
    offline_message_key = "logs.tiktok.stream_offline"
    offline_placeholder = "{unique_id}"
    sign_api_key_setting = "tiktok_sign_api_key"

    def _normalize_target(self, target: str) -> str:
        return target.strip().lstrip("@")

    def _create_worker(self, target: str) -> QThread:
        from backend.workers import TikTokChatWorker

        sign_api_key = self._config.load_string(self.sign_api_key_setting, "").strip()
        return TikTokChatWorker(
            target_channel=target,
            sign_api_key=sign_api_key or None,
            i18n=self._i18n,
        )

    def _describe_stream(self, stream_info: dict) -> tuple[str, str, str]:
        unique_id = stream_info.get("unique_id", "") or stream_info.get("channel", "") or "TikTok Live"
        return unique_id, unique_id, f"[TikTok] Connected to TikTok Live: '@{unique_id}'."
