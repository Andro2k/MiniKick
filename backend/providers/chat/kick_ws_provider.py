# backend\providers\chat\kick_ws_provider.py

import logging
import time
import uuid
import socket
from datetime import datetime, timezone
from backend.utils.json_utils import parse_kick_payload, fast_dumps
from collections import deque
import websocket
from typing import Callable
from backend.models import AlertEvent, AlertType

logger = logging.getLogger("minikick.providers.kick_ws_provider")

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
}

DEFAULT_KICK_COLOR = "#2ECD70"

class KickWebSocketManager:
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key
        self._running = False
        self.ws: websocket.WebSocketApp | None = None
        self._room_id = 0
        self._channel_id = 0
        self._last_followers_count: int | None = None
        self._seen_message_ids = deque(maxlen=1000)
        self._seen_message_ids_set = set()
        self._callback: Callable | None = None
        self._on_poll_update: Callable[[dict], None] | None = None
        self._on_poll_delete: Callable[[], None] | None = None
        self._on_pinned_created: Callable[[dict], None] | None = None
        self._on_pinned_deleted: Callable[[], None] | None = None
        self._on_alert: Callable[[AlertEvent], None] | None = None
        self._on_reward: Callable[[str, str, str], None] | None = None
        self._on_message_deleted: Callable[[str], None] | None = None
        self._on_user_banned: Callable[[str], None] | None = None
        self._dispatch_table: dict[str, Callable[[dict, websocket.WebSocketApp], None]] = {
            "App\\Events\\ChatMessageEvent": self._handle_chat_message,
            "App\\Events\\PollUpdateEvent": self._handle_poll_update,
            "App\\Events\\PollDeleteEvent": self._handle_poll_delete,
            "App\\Events\\PinnedMessageCreatedEvent": self._handle_pinned_created,
            "App\\Events\\PinnedMessageDeletedEvent": self._handle_pinned_deleted,
            "App\\Events\\SubscriptionEvent": self._handle_subscription,
            "App\\Events\\ChannelSubscriptionEvent": self._handle_subscription,
            "App\\Events\\GiftedSubscriptionsEvent": self._handle_gifted_subscriptions,
            "App\\Events\\LuckyUsersWhoGotGiftSubscriptionsEvent": self._handle_gifted_subscriptions,
            "App\\Events\\StreamHostEvent": self._handle_stream_host,
            "App\\Events\\FollowersUpdated": self._handle_followers_updated,
            "FollowersUpdated": self._handle_followers_updated,
            "followers.updated": self._handle_followers_updated,
            "channel.followed": self._handle_followers_updated,
            "GoalProgressUpdateEvent": self._handle_goal_progress_update,
            "App\\Events\\GoalProgressUpdateEvent": self._handle_goal_progress_update,
            "RewardRedeemedEvent": self._handle_reward_redeemed,
            "App\\Events\\RewardRedeemedEvent": self._handle_reward_redeemed,
            "App\\Events\\ChatMessageDeletedEvent": self._handle_message_deleted,
            "App\\Events\\MessageDeletedEvent": self._handle_message_deleted,
            "MessageDeletedEvent": self._handle_message_deleted,
            "App\\Events\\UserBannedEvent": self._handle_user_banned,
            "UserBannedEvent": self._handle_user_banned,
            "pusher:connection_established": self._handle_connection_established,
            "pusher:ping": self._handle_ping,
        }

    def start_socket(
        self,
        room_id: int,
        channel_id: int = 0,
        initial_followers: int | None = None,
        on_message: Callable[[str, str, list, str, str, int], None] | None = None,
        on_poll_update: Callable[[dict], None] | None = None,
        on_poll_delete: Callable[[], None] | None = None,
        on_pinned_created: Callable[[dict], None] | None = None,
        on_pinned_deleted: Callable[[], None] | None = None,
        on_alert: Callable[[AlertEvent], None] | None = None,
        on_reward_redeemed: Callable[[str, str, str], None] | None = None,
        on_message_deleted: Callable[[str], None] | None = None,
        on_user_banned: Callable[[str], None] | None = None,
    ) -> None:
        self._room_id = room_id
        self._channel_id = channel_id
        if initial_followers is not None and self._last_followers_count is None:
            self._last_followers_count = initial_followers
        self._callback = on_message
        self._on_poll_update = on_poll_update
        self._on_poll_delete = on_poll_delete
        self._on_pinned_created = on_pinned_created
        self._on_pinned_deleted = on_pinned_deleted
        self._on_alert = on_alert
        self._on_reward = on_reward_redeemed
        self._on_message_deleted = on_message_deleted
        self._on_user_banned = on_user_banned
        self._running = True
        
        url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        logger.info("[KickWebSocket] Connecting to Pusher WebSocket for room_id=%s...", room_id)
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self._on_raw_frame,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever(
            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),),
            ping_interval=30,
            ping_timeout=10
        )

    def _on_error(self, ws: websocket.WebSocketApp, err: Exception) -> None:
        logger.error(
            "[KickWebSocket] WebSocket error (%s): %s",
            type(err).__name__,
            err,
            exc_info=not isinstance(err, (KeyboardInterrupt, SystemExit))
        )

    def _on_close(self, ws: websocket.WebSocketApp, status: int | None, msg: str | None) -> None:
        meaning = RFC_6455_CLOSE_CODES.get(status, "Unknown/Unregistered") if status is not None else "Clean/No Code"
        logger.info("[KickWebSocket] WebSocket closed: code=%s (%s), reason=%s", status, meaning, msg or "N/A")

    def _on_raw_frame(self, ws: websocket.WebSocketApp, raw: str) -> None:
        if not self._running:
            return

        try:
            event, inner = parse_kick_payload(raw)
            if not event:
                return
            handler = self._dispatch_table.get(event)
            if handler:
                handler(inner, ws)
            elif not event.startswith("pusher:"):
                logger.debug("[KickWebSocket] Pusher unhandled event: %s | data: %s", event, str(inner)[:200])

        except Exception as e:
            logger.debug("[KickWebSocket] Notice processing frame: %s", e)

    def _handle_chat_message(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        sender = inner.get("sender")
        if not isinstance(sender, dict):
            return

        user = sender.get("username", "")
        msg = inner.get("content", "")
        if not user or not msg:
            return

        msg_id = inner.get("id", "")
        if msg_id:
            if msg_id in self._seen_message_ids_set:
                return
            if len(self._seen_message_ids) == self._seen_message_ids.maxlen:
                oldest = self._seen_message_ids.popleft()
                self._seen_message_ids_set.discard(oldest)
            self._seen_message_ids.append(msg_id)
            self._seen_message_ids_set.add(msg_id)

        created_at = inner.get("created_at", "")
        latency_info = ""
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                now_utc = datetime.now(timezone.utc)
                latency = (now_utc - created_dt).total_seconds()
                latency_info = f" (server latency: {latency:.3f}s)"
            except Exception:
                pass

        logger.info("[KickWebSocket] Chat message received: '%s' from '%s'%s", msg, user, latency_info)

        identity = sender.get("identity")
        badges = []
        color = DEFAULT_KICK_COLOR

        if isinstance(identity, dict):
            color = identity.get("color") or DEFAULT_KICK_COLOR
            raw_badges = identity.get("badges")
            if isinstance(raw_badges, list):
                for b in raw_badges:
                    if isinstance(b, dict) and "type" in b:
                        badges.append(b["type"])

            badges_v2 = identity.get("badges_v2")
            if isinstance(badges_v2, list):
                for b in badges_v2:
                    if isinstance(b, dict) and b.get("name") == "level":
                        meta = b.get("metadata")
                        if isinstance(meta, dict):
                            lvl = meta.get("level")
                            if lvl is not None:
                                badges.append(f"level_{lvl}")

        sender_id = sender.get("id", 0)

        if self._callback:
            self._callback(user, msg, badges, color, msg_id, sender_id)

    def _handle_poll_update(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        poll_data = inner.get("poll") or inner
        if poll_data and self._on_poll_update:
            self._on_poll_update(poll_data)

    def _handle_poll_delete(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if self._on_poll_delete:
            self._on_poll_delete()

    def _handle_pinned_created(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        pinned = inner.get("pinned_message") or inner
        if isinstance(pinned, dict):
            msg_obj = pinned.get("message")
            if isinstance(msg_obj, dict):
                content = str(msg_obj.get("content", ""))
                sender = msg_obj.get("sender") or pinned.get("sender") or {}
            elif isinstance(pinned.get("content"), dict):
                content = str(pinned.get("content", {}).get("content", ""))
                sender = pinned.get("content", {}).get("sender") or pinned.get("sender") or {}
            else:
                content = str(pinned.get("content") or pinned.get("message") or "")
                sender = pinned.get("sender") or {}

            normalized = {
                "id": pinned.get("id") or (msg_obj.get("id") if isinstance(msg_obj, dict) else ""),
                "content": content,
                "sender": sender
            }
            if self._on_pinned_created:
                self._on_pinned_created(normalized)

    def _handle_pinned_deleted(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if self._on_pinned_deleted:
            self._on_pinned_deleted()

    def _handle_subscription(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if not self._on_alert:
            return
        user = inner.get("username", "") or inner.get("user", {}).get("username", "")
        if not user:
            return
        months = int(inner.get("months", 1))
        alert_type = AlertType.RESUB if months > 1 else AlertType.SUBSCRIPTION
        event = AlertEvent(
            event_id=f"kick_sub_{inner.get('id', uuid.uuid4().hex[:8])}",
            platform="kick",
            alert_type=alert_type,
            username=user,
            display_name=user,
            amount=months,
            tier="1",
            timestamp=time.time()
        )
        self._on_alert(event)

    def _handle_gifted_subscriptions(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if not self._on_alert:
            return
        gifter = inner.get("gifter_username") or inner.get("username") or "Anónimo"
        recipients = inner.get("gifted_usernames", [])
        amount = len(recipients) if isinstance(recipients, list) and recipients else int(inner.get("count", 1))
        event = AlertEvent(
            event_id=f"kick_gift_{inner.get('id', uuid.uuid4().hex[:8])}",
            platform="kick",
            alert_type=AlertType.SUB_GIFT,
            username=gifter,
            display_name=gifter,
            amount=amount,
            tier="1",
            timestamp=time.time()
        )
        self._on_alert(event)

    def _handle_stream_host(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if not self._on_alert:
            return
        host_user = inner.get("host_username") or inner.get("username") or "Streamer"
        viewers = int(inner.get("number_viewers", 1))
        event = AlertEvent(
            event_id=f"kick_host_{inner.get('id', uuid.uuid4().hex[:8])}",
            platform="kick",
            alert_type=AlertType.RAID,
            username=host_user,
            display_name=host_user,
            amount=viewers,
            timestamp=time.time()
        )
        self._on_alert(event)

    def _handle_followers_updated(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if not self._on_alert:
            return
        if inner.get("followed") is False:
            return
        user = inner.get("username") or inner.get("follower", {}).get("username", "") or "Nuevo Seguidor"
        event = AlertEvent(
            event_id=f"kick_follow_{inner.get('id', uuid.uuid4().hex[:8])}",
            platform="kick",
            alert_type=AlertType.FOLLOW,
            username=user,
            display_name=user,
            amount=1,
            timestamp=time.time()
        )
        self._on_alert(event)

    def _handle_goal_progress_update(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if inner.get("type") != "followers":
            return
        
        current_val = inner.get("current_value")
        if not isinstance(current_val, (int, float)):
            return

        current_count = int(current_val)
        if self._last_followers_count is not None and current_count > self._last_followers_count:
            logger.info("[KickWebSocket] Follower count increase detected: %d -> %d", self._last_followers_count, current_count)
            if self._on_alert:
                event = AlertEvent(
                    event_id=f"kick_follow_{int(time.time())}",
                    platform="kick",
                    alert_type=AlertType.FOLLOW,
                    username="Nuevo Seguidor",
                    display_name="Nuevo Seguidor",
                    amount=1,
                    timestamp=time.time()
                )
                self._on_alert(event)

        self._last_followers_count = current_count

    def _handle_reward_redeemed(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        reward_title = inner.get("reward_title", "") or inner.get("reward", {}).get("title", "")
        username = inner.get("username", "") or inner.get("user", {}).get("username", "")
        user_input = inner.get("user_input", "") or inner.get("message", "") or ""
        if reward_title and username and self._on_reward:
            logger.info("[KickWebSocket] Real-time reward redeemed: '%s' by %s (input: '%s')", reward_title, username, user_input)
            self._on_reward(username, reward_title, user_input)

    def _handle_message_deleted(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        msg_id = inner.get("message", {}).get("id") or inner.get("id", "")
        if msg_id:
            logger.info("[KickWebSocket] Message deleted event received: %s", msg_id)
            if self._on_message_deleted:
                self._on_message_deleted(msg_id)

    def _handle_user_banned(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        user = inner.get("user", {}) if isinstance(inner.get("user"), dict) else inner
        username = user.get("username") or inner.get("username", "")
        if username:
            logger.info("[KickWebSocket] User banned/timeout event received: %s", username)
            if self._on_user_banned:
                self._on_user_banned(username)

    def _handle_connection_established(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        logger.info("[KickWebSocket] Pusher connection established. Subscribing to room_id=%s, channel_id=%s", self._room_id, self._channel_id)
        channels = [
            f"chatrooms.{self._room_id}.v2",
            f"chatroom_{self._room_id}",
        ]
        if self._channel_id:
            channels.append(f"channel_{self._channel_id}")
            channels.append(f"channel.{self._channel_id}")

        for ch in channels:
            logger.info("[KickWebSocket] Subscribing to topic: %s", ch)
            if ws:
                ws.send(fast_dumps({
                    "event": "pusher:subscribe",
                    "data": {"channel": ch}
                }))

    def _handle_ping(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        if ws:
            ws.send('{"event":"pusher:pong"}')

    def stop_socket(self) -> None:
        self._running = False
        logger.info("[KickWebSocket] Stopping Pusher socket...")
        if self.ws:
            self.ws.keep_running = False
            if self.ws.sock and self.ws.sock.connected:
                self.ws.sock.close()
