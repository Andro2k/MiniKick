# backend\workers\twitch_rewards_worker.py

import logging
from PySide6.QtCore import QThread, Signal
from backend.providers.chat import TwitchEventSubProvider
from backend.services.system import TranslationService
from backend.utils.worker_utils import ExponentialBackoff

logger = logging.getLogger("minikick.workers.twitch_rewards")

class TwitchRewardWorker(QThread):
    reward_redeemed = Signal(str, str, str)
    alert_received = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, i18n, auth_manager, client_id: str, broadcaster_id: str, provider=None, parent=None):
        super().__init__(parent)
        self.i18n = i18n or TranslationService()
        self.auth_manager = auth_manager
        self.client_id = client_id
        self.broadcaster_id = str(broadcaster_id)
        self.setObjectName("Worker_Twitch_EventSub_Rewards")
        self._running = False
        self.provider = provider or TwitchEventSubProvider(i18n=self.i18n)
        self._backoff = ExponentialBackoff(initial=2.0, max_backoff=30.0, factor=1.5, jitter=0.2)

    def run(self):
        self._running = True
        logger.info("[TwitchRewardWorker] Starting Twitch EventSub worker thread...")

        def _on_connected():
            self._backoff.reset()
            logger.info("[TwitchRewardWorker] EventSub connected and ready.")

        def _on_reward(user_name: str, reward_title: str, user_input: str):
            if self._running:
                self.reward_redeemed.emit(user_name, reward_title, user_input)

        def _on_alert(alert_event):
            if self._running:
                self.alert_received.emit(alert_event)

        def _on_error(err_str: str):
            if self._running:
                self.error_occurred.emit(err_str)

        while self._running and not self.isInterruptionRequested():
            try:
                tokens = self.auth_manager.get_tokens() if hasattr(self.auth_manager, "get_tokens") else {}
                access_token = tokens.get("access_token", "")
                if not access_token:
                    logger.warning("[TwitchRewardWorker] No valid access token available for EventSub.")
                    self.msleep(5000)
                    continue

                self.provider.start_socket(
                    broadcaster_id=self.broadcaster_id,
                    client_id=self.client_id,
                    access_token=access_token,
                    on_reward_redeemed=_on_reward,
                    on_alert_received=_on_alert,
                    on_connected=_on_connected,
                    on_error=_on_error
                )
            except Exception as e:
                logger.error("[TwitchRewardWorker] Unhandled exception in worker: %s", e)
                if self._running:
                    self.error_occurred.emit(str(e))

            if not self._running or self.isInterruptionRequested():
                break

            delay_sec = self._backoff.next_delay()
            logger.debug("[TwitchRewardWorker] Reconnecting in %.1fs (attempt #%s)...", delay_sec, self._backoff.attempts)
            self.msleep(int(delay_sec * 1000))

    def stop(self):
        self._running = False
        self.requestInterruption()
        if self.provider:
            self.provider.stop_socket()
