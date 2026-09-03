# backend\providers\chat\kick_websocket.py

import re
import logging
import time
import uuid
from backend.utils.json_utils import parse_kick_payload, fast_dumps
import websocket
from typing import Callable
from frontend.common.theme import COLOR_GREEN
from backend.models.alert_models import AlertEvent, AlertType

logger = logging.getLogger("minikick.providers.kick_websocket")

FOLLOW_BOT_REGEX = re.compile(
    r"(?:gracias\s+por\s+segu(?:ir|irme)|thanks\s+(?:you\s+)?for\s+following|thank\s+you\s+for\s+following|gracias\s+por\s+el\s+follow)[,\s:]+@?([a-zA-Z0-9_]+)",
    re.IGNORECASE
)

class KickWebSocketManager:
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key
        self._running = False
        self.ws: websocket.WebSocketApp | None = None
        self._room_id = 0
        self._channel_id = 0
        self._last_followers_count: int | None = None
        self._pending_follower_name: str | None = None
        self._pending_follower_time: float = 0.0
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
            on_error=lambda ws, err: logger.error("[KickWebSocket] WebSocket error: %s", err),
            on_close=lambda ws, status, msg: logger.info("[KickWebSocket] WebSocket closed: status=%s msg=%s", status, msg)
        )
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

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

        identity = sender.get("identity")
        badges = []
        color = COLOR_GREEN

        if isinstance(identity, dict):
            color = identity.get("color") or COLOR_GREEN
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

        msg_id = inner.get("id", "")
        sender_id = sender.get("id", 0)

        if self._callback:
            self._callback(user, msg, badges, color, msg_id, sender_id)

        match = FOLLOW_BOT_REGEX.search(msg)
        if match:
            new_follower = match.group(1).strip()
            if new_follower and new_follower.lower() != user.lower():
                logger.info("[KickWebSocket] Detected follow greeting in chat for user: %s", new_follower)
                self._pending_follower_name = new_follower
                self._pending_follower_time = time.time()
                if self._on_alert:
                    event = AlertEvent(
                        event_id=f"kick_follow_{new_follower.lower()}_{int(time.time() / 15)}",
                        platform="kick",
                        alert_type=AlertType.FOLLOW,
                        username=new_follower,
                        display_name=new_follower,
                        amount=1,
                        timestamp=time.time()
                    )
                    self._on_alert(event)

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
            follower_name = "Nuevo Seguidor"
            if self._pending_follower_name and (time.time() - self._pending_follower_time < 6.0):
                follower_name = self._pending_follower_name
            
            if self._on_alert:
                event = AlertEvent(
                    event_id=f"kick_follow_{follower_name.lower()}_{int(time.time() / 15)}",
                    platform="kick",
                    alert_type=AlertType.FOLLOW,
                    username=follower_name,
                    display_name=follower_name,
                    amount=1,
                    timestamp=time.time()
                )
                self._on_alert(event)

        self._last_followers_count = current_count

    def _handle_reward_redeemed(self, inner: dict, ws: websocket.WebSocketApp) -> None:
        reward_title = inner.get("reward_title", "")
        username = inner.get("username", "")
        user_input = inner.get("user_input", "")
        if reward_title and username and self._on_reward:
            logger.info("[KickWebSocket] Real-time reward redeemed: '%s' by %s", reward_title, username)
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
        logger.info("[KickWebSocket] Pusher connection established. Subscribing to chatrooms.%s.v2", self._room_id)
        channels = [
            f"chatrooms.{self._room_id}.v2",
            f"chatroom_{self._room_id}",
        ]
        if self._channel_id:
            channels.extend([
                f"channel_{self._channel_id}",
                f"channel.{self._channel_id}",
            ])

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
