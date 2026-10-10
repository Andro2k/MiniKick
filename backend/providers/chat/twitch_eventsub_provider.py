# backend\providers\chat\twitch_eventsub_provider.py

import logging
import threading
import time
from collections import deque
from typing import Callable
import requests
import websocket

from backend.models import AlertEvent, AlertType
from backend.services.system import TranslationService
from backend.utils.json_utils import fast_loads
from .base_chat_provider import BaseChatSocketProvider

logger = logging.getLogger("minikick.providers.twitch_eventsub")

TWITCH_EVENTSUB_WS_URL = "wss://eventsub.wss.twitch.tv/ws"
TWITCH_EVENTSUB_API_URL = "https://api.twitch.tv/helix/eventsub/subscriptions"

RFC_6455_CLOSE_CODES: dict[int, str] = {
    1000: "Normal Closure",
    1001: "Going Away",
    1002: "Protocol Error",
    1003: "Unsupported Data",
    1005: "No Status Received",
    1006: "Abnormal Closure",
    1007: "Invalid frame payload data",
    1008: "Policy Violation",
    1009: "Message Too Big",
    1011: "Internal Server Error",
    1012: "Service Restart",
    1013: "Try Again Later",
    1015: "TLS Handshake Failure",
    4000: "Internal Error",
    4001: "Client Sent Inbound Traffic",
    4002: "Client Failed Ping-Pong",
    4003: "Connection Unused",
    4004: "Reconnect Grace Time Expired",
    4005: "Network Timeout",
    4006: "Network Error",
    4007: "Invalid Reconnect",
}

class TwitchEventSubProvider(BaseChatSocketProvider):
    def __init__(self, i18n=None) -> None:
        self.i18n = i18n or TranslationService()
        self._running = False
        self.ws: websocket.WebSocketApp | None = None
        self._broadcaster_id = ""
        self._client_id = ""
        self._access_token = ""
        self._seen_message_ids = deque(maxlen=1000)
        self._seen_message_ids_set: set[str] = set()
        self._on_reward_redeemed: Callable[[str, str, str], None] | None = None
        self._on_alert_received: Callable[[AlertEvent], None] | None = None
        self._on_connected: Callable[[], None] | None = None
        self._on_disconnected: Callable[[], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._sub_threads: list[threading.Thread] = []

    @property
    def is_running(self) -> bool:
        return self._running

    def start_socket(
        self,
        broadcaster_id: str,
        client_id: str,
        access_token: str,
        on_reward_redeemed: Callable[[str, str, str], None] | None = None,
        on_alert_received: Callable[[AlertEvent], None] | None = None,
        on_connected: Callable[[], None] | None = None,
        on_disconnected: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._broadcaster_id = str(broadcaster_id).strip()
        self._client_id = client_id.strip()
        self._access_token = access_token.strip()
        self._on_reward_redeemed = on_reward_redeemed
        self._on_alert_received = on_alert_received
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_error = on_error
        self._running = True

        logger.info(
            "[TwitchEventSub] Connecting to Twitch EventSub WebSocket for broadcaster_id=%s...",
            self._broadcaster_id
        )

        self.ws = websocket.WebSocketApp(
            TWITCH_EVENTSUB_WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error_handler,
            on_close=self._on_close_handler
        )
        self.ws.run_forever(ping_interval=20, ping_timeout=10)

    def _on_open(self, _ws: websocket.WebSocketApp) -> None:
        logger.info("[TwitchEventSub] WebSocket connection open. Awaiting session_welcome...")
        if self._on_connected:
            try:
                self._on_connected()
            except Exception as e:
                logger.debug("[TwitchEventSub] Exception in on_connected callback: %s", e)

    def _on_message(self, _ws: websocket.WebSocketApp, raw_msg: str) -> None:
        if not self._running:
            return

        try:
            msg = fast_loads(raw_msg)
        except Exception:
            return

        metadata = msg.get("metadata", {})
        msg_type = metadata.get("message_type")
        payload = msg.get("payload", {})
        msg_id = metadata.get("message_id", "")

        if msg_id:
            if msg_id in self._seen_message_ids_set:
                return
            if len(self._seen_message_ids) == self._seen_message_ids.maxlen:
                oldest = self._seen_message_ids.popleft()
                self._seen_message_ids_set.discard(oldest)
            self._seen_message_ids.append(msg_id)
            self._seen_message_ids_set.add(msg_id)

        if msg_type == "session_welcome":
            session_id = payload.get("session", {}).get("id")
            if session_id:
                logger.info("[TwitchEventSub] Session established: %s. Spawning non-blocking subscription dispatcher...", session_id)
                self._dispatch_subscriptions_async(session_id)

        elif msg_type == "notification":
            self._handle_notification(metadata, payload)

        elif msg_type == "session_keepalive":
            logger.debug("[TwitchEventSub] Session keepalive received.")

        elif msg_type == "session_reconnect":
            reconnect_url = payload.get("session", {}).get("reconnect_url")
            logger.info("[TwitchEventSub] Twitch requested reconnect to: %s", reconnect_url)

    def _dispatch_subscriptions_async(self, session_id: str) -> None:
        sub_thread = threading.Thread(
            target=self._subscribe_all_events,
            args=(session_id, self._client_id, self._access_token, self._broadcaster_id),
            name=f"TwitchEventSubSubscribe-{session_id[:8]}",
            daemon=True
        )
        self._sub_threads.append(sub_thread)
        sub_thread.start()

    def _subscribe_all_events(self, session_id: str, client_id: str, access_token: str, broadcaster_id: str) -> None:
        if not (session_id and client_id and access_token and broadcaster_id):
            return

        headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        subscriptions = [
            ("channel.channel_points_custom_reward_redemption.add", "1", {"broadcaster_user_id": broadcaster_id}),
            ("channel.follow", "2", {"broadcaster_user_id": broadcaster_id, "moderator_user_id": broadcaster_id}),
            ("channel.subscribe", "1", {"broadcaster_user_id": broadcaster_id}),
            ("channel.subscription.message", "1", {"broadcaster_user_id": broadcaster_id}),
            ("channel.subscription.gift", "1", {"broadcaster_user_id": broadcaster_id}),
            ("channel.cheer", "1", {"broadcaster_user_id": broadcaster_id}),
            ("channel.raid", "1", {"to_broadcaster_user_id": broadcaster_id})
        ]

        for sub_type, ver, cond in subscriptions:
            if not self._running:
                break
            body = {
                "type": sub_type,
                "version": ver,
                "condition": cond,
                "transport": {
                    "method": "websocket",
                    "session_id": session_id
                }
            }
            try:
                resp = requests.post(TWITCH_EVENTSUB_API_URL, headers=headers, json=body, timeout=6)
                if resp.status_code in (200, 202):
                    logger.debug("[TwitchEventSub] Subscribed to %s (status=%s)", sub_type, resp.status_code)
                elif resp.status_code == 409:
                    logger.debug("[TwitchEventSub] Subscription %s already active (409 Conflict)", sub_type)
                else:
                    logger.warning("[TwitchEventSub] Subscription %s returned status %s: %s", sub_type, resp.status_code, resp.text[:200])
            except Exception as sub_err:
                logger.debug("[TwitchEventSub] Error subscribing to EventSub %s: %s", sub_type, sub_err)

    def _handle_notification(self, metadata: dict, payload: dict) -> None:
        sub_type = metadata.get("subscription_type", "")
        event = payload.get("event", {})
        now_ts = int(time.time())

        anon_user = self.i18n.get("common.anonymous") if hasattr(self.i18n, "get") else "Anonymous"
        follower_label = self.i18n.get("common.follower") if hasattr(self.i18n, "get") else "Follower"
        subscriber_label = self.i18n.get("common.subscriber") if hasattr(self.i18n, "get") else "Subscriber"
        streamer_label = self.i18n.get("common.streamer") if hasattr(self.i18n, "get") else "Streamer"

        if sub_type == "channel.channel_points_custom_reward_redemption.add":
            user_name = event.get("user_name") or event.get("user_login") or anon_user
            reward_title = event.get("reward", {}).get("title", "")
            user_input = event.get("user_input", "")
            if reward_title and self._on_reward_redeemed:
                logger.info("[TwitchEventSub] Redemption detected: user='%s', reward='%s'", user_name, reward_title)
                self._on_reward_redeemed(user_name, reward_title, user_input)

        elif sub_type == "channel.follow":
            user = event.get("user_name") or event.get("user_login") or follower_label
            alert = AlertEvent(
                event_id=f"twitch_follow_{event.get('user_id', '')}_{now_ts}",
                platform="twitch",
                alert_type=AlertType.FOLLOW,
                username=user,
                display_name=user,
                amount=1
            )
            self._emit_alert(alert)

        elif sub_type == "channel.subscribe":
            user = event.get("user_name") or event.get("user_login") or subscriber_label
            tier = str(event.get("tier", "1000"))[0]
            alert = AlertEvent(
                event_id=f"twitch_sub_{event.get('user_id', '')}_{now_ts}",
                platform="twitch",
                alert_type=AlertType.SUBSCRIPTION,
                username=user,
                display_name=user,
                tier=tier,
                amount=1
            )
            self._emit_alert(alert)

        elif sub_type == "channel.subscription.message":
            user = event.get("user_name") or event.get("user_login") or subscriber_label
            months = int(event.get("cumulative_months", 1))
            msg_text = event.get("message", {}).get("text", "")
            tier = str(event.get("tier", "1000"))[0]
            alert = AlertEvent(
                event_id=f"twitch_resub_{event.get('user_id', '')}_{now_ts}",
                platform="twitch",
                alert_type=AlertType.RESUB,
                username=user,
                display_name=user,
                message=msg_text,
                amount=months,
                tier=tier
            )
            self._emit_alert(alert)

        elif sub_type == "channel.subscription.gift":
            user = event.get("user_name") or event.get("user_login") or anon_user
            total = int(event.get("total", 1))
            tier = str(event.get("tier", "1000"))[0]
            alert = AlertEvent(
                event_id=f"twitch_gift_{event.get('user_id', '')}_{now_ts}",
                platform="twitch",
                alert_type=AlertType.SUB_GIFT,
                username=user,
                display_name=user,
                amount=total,
                tier=tier
            )
            self._emit_alert(alert)

        elif sub_type == "channel.cheer":
            user = event.get("user_name") or event.get("user_login") or anon_user
            bits = int(event.get("bits", 0))
            msg_text = event.get("message", "")
            alert = AlertEvent(
                event_id=f"twitch_cheer_{event.get('user_id', '')}_{now_ts}",
                platform="twitch",
                alert_type=AlertType.CHEER,
                username=user,
                display_name=user,
                amount=bits,
                message=msg_text
            )
            self._emit_alert(alert)

        elif sub_type == "channel.raid":
            user = event.get("from_broadcaster_user_name") or event.get("from_broadcaster_user_login") or streamer_label
            viewers = int(event.get("viewers", 1))
            alert = AlertEvent(
                event_id=f"twitch_raid_{event.get('from_broadcaster_user_id', '')}_{now_ts}",
                platform="twitch",
                alert_type=AlertType.RAID,
                username=user,
                display_name=user,
                amount=viewers
            )
            self._emit_alert(alert)

    def _emit_alert(self, alert: AlertEvent) -> None:
        if self._on_alert_received:
            try:
                self._on_alert_received(alert)
            except Exception as e:
                logger.debug("[TwitchEventSub] Exception in on_alert_received callback: %s", e)

    def _on_error_handler(self, _ws: websocket.WebSocketApp, error: Exception) -> None:
        if not self._running:
            return
        is_routine_network_drop = isinstance(
            error,
            (websocket.WebSocketTimeoutException, TimeoutError, ConnectionResetError, BrokenPipeError)
        )
        log_func = logger.warning if is_routine_network_drop else logger.error
        log_func(
            "[TwitchEventSub] WebSocket error (%s): %s",
            type(error).__name__,
            error,
            exc_info=not is_routine_network_drop and not isinstance(error, (KeyboardInterrupt, SystemExit))
        )
        if self._on_error:
            self._on_error(str(error))

    def _on_close_handler(self, _ws: websocket.WebSocketApp, close_code: int | None, close_msg: str | None) -> None:
        meaning = RFC_6455_CLOSE_CODES.get(close_code, "Unknown/Unregistered") if close_code is not None else "Clean/No Code"
        logger.info("[TwitchEventSub] Connection closed: code=%s (%s), reason=%s", close_code, meaning, close_msg or "N/A")
        if self._on_disconnected:
            try:
                self._on_disconnected()
            except Exception:
                pass

    def stop_socket(self) -> None:
        self._running = False
        logger.info("[TwitchEventSub] Stopping Twitch EventSub WebSocket...")
        if self.ws:
            try:
                self.ws.keep_running = False
                if self.ws.sock and self.ws.sock.connected:
                    self.ws.sock.close()
                self.ws.close()
            except Exception:
                pass
