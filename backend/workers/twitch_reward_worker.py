# backend\workers\twitch_reward_worker.py

import logging
import time
from PySide6.QtCore import QThread, Signal
from backend.utils.json_utils import fast_loads
from backend.models.alert_models import AlertEvent, AlertType

logger = logging.getLogger("minikick.workers.twitch_rewards")

class TwitchRewardWorker(QThread):
    reward_redeemed = Signal(str, str, str)
    alert_received = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, i18n, auth_manager, client_id: str, broadcaster_id: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.auth_manager = auth_manager
        self.client_id = client_id
        self.broadcaster_id = str(broadcaster_id)
        self.setObjectName("Worker_Twitch_EventSub_Rewards")
        self._running = False
        self._ws = None

    def run(self):
        import websocket
        import requests

        self._running = True

        def on_message(ws, msg_str):
            try:
                msg = fast_loads(msg_str)
            except Exception:
                return

            metadata = msg.get("metadata", {})
            msg_type = metadata.get("message_type")
            payload = msg.get("payload", {})

            if msg_type == "session_welcome":
                session_id = payload.get("session", {}).get("id")
                tokens = self.auth_manager.get_tokens() if hasattr(self.auth_manager, "get_tokens") else {}
                access_token = tokens.get("access_token", "")
                if session_id and access_token and self.client_id and self.broadcaster_id:
                    headers = {
                        "Client-ID": self.client_id,
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                    subscriptions = [
                        ("channel.channel_points_custom_reward_redemption.add", "1", {"broadcaster_user_id": self.broadcaster_id}),
                        ("channel.follow", "2", {"broadcaster_user_id": self.broadcaster_id, "moderator_user_id": self.broadcaster_id}),
                        ("channel.subscribe", "1", {"broadcaster_user_id": self.broadcaster_id}),
                        ("channel.subscription.message", "1", {"broadcaster_user_id": self.broadcaster_id}),
                        ("channel.subscription.gift", "1", {"broadcaster_user_id": self.broadcaster_id}),
                        ("channel.cheer", "1", {"broadcaster_user_id": self.broadcaster_id}),
                        ("channel.raid", "1", {"to_broadcaster_user_id": self.broadcaster_id})
                    ]
                    for sub_type, ver, cond in subscriptions:
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
                            requests.post("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers, json=body, timeout=6)
                        except Exception as sub_err:
                            logger.debug("[TwitchRewardWorker] Note subscribing EventSub %s: %s", sub_type, sub_err)

            elif msg_type == "notification":
                sub_type = metadata.get("subscription_type", "")
                event = payload.get("event", {})
                if sub_type == "channel.channel_points_custom_reward_redemption.add":
                    user_name = event.get("user_name") or event.get("user_login") or "Anónimo"
                    reward_title = event.get("reward", {}).get("title", "")
                    user_input = event.get("user_input", "")
                    if reward_title:
                        logger.info("[TwitchRewardWorker] Canje detectado (Twitch): usuario='%s', recompensa='%s'", user_name, reward_title)
                        self.reward_redeemed.emit(user_name, reward_title, user_input)
                elif sub_type == "channel.follow":
                    user = event.get("user_name") or event.get("user_login") or "Seguidor"
                    alert = AlertEvent(
                        event_id=f"twitch_follow_{event.get('user_id', '')}_{int(time.time())}",
                        platform="twitch",
                        alert_type=AlertType.FOLLOW,
                        username=user,
                        display_name=user,
                        amount=1
                    )
                    self.alert_received.emit(alert)
                elif sub_type == "channel.subscribe":
                    user = event.get("user_name") or event.get("user_login") or "Suscriptor"
                    tier = str(event.get("tier", "1000"))[0]
                    alert = AlertEvent(
                        event_id=f"twitch_sub_{event.get('user_id', '')}_{int(time.time())}",
                        platform="twitch",
                        alert_type=AlertType.SUBSCRIPTION,
                        username=user,
                        display_name=user,
                        tier=tier,
                        amount=1
                    )
                    self.alert_received.emit(alert)
                elif sub_type == "channel.subscription.message":
                    user = event.get("user_name") or event.get("user_login") or "Suscriptor"
                    months = int(event.get("cumulative_months", 1))
                    msg_text = event.get("message", {}).get("text", "")
                    tier = str(event.get("tier", "1000"))[0]
                    alert = AlertEvent(
                        event_id=f"twitch_resub_{event.get('user_id', '')}_{int(time.time())}",
                        platform="twitch",
                        alert_type=AlertType.RESUB,
                        username=user,
                        display_name=user,
                        message=msg_text,
                        amount=months,
                        tier=tier
                    )
                    self.alert_received.emit(alert)
                elif sub_type == "channel.subscription.gift":
                    user = event.get("user_name") or event.get("user_login") or "Anónimo"
                    total = int(event.get("total", 1))
                    tier = str(event.get("tier", "1000"))[0]
                    alert = AlertEvent(
                        event_id=f"twitch_gift_{event.get('user_id', '')}_{int(time.time())}",
                        platform="twitch",
                        alert_type=AlertType.SUB_GIFT,
                        username=user,
                        display_name=user,
                        amount=total,
                        tier=tier
                    )
                    self.alert_received.emit(alert)
                elif sub_type == "channel.cheer":
                    user = event.get("user_name") or event.get("user_login") or "Anónimo"
                    bits = int(event.get("bits", 0))
                    msg_text = event.get("message", "")
                    alert = AlertEvent(
                        event_id=f"twitch_cheer_{event.get('user_id', '')}_{int(time.time())}",
                        platform="twitch",
                        alert_type=AlertType.CHEER,
                        username=user,
                        display_name=user,
                        amount=bits,
                        message=msg_text
                    )
                    self.alert_received.emit(alert)
                elif sub_type == "channel.raid":
                    user = event.get("from_broadcaster_user_name") or event.get("from_broadcaster_user_login") or "Streamer"
                    viewers = int(event.get("viewers", 1))
                    alert = AlertEvent(
                        event_id=f"twitch_raid_{event.get('from_broadcaster_user_id', '')}_{int(time.time())}",
                        platform="twitch",
                        alert_type=AlertType.RAID,
                        username=user,
                        display_name=user,
                        amount=viewers
                    )
                    self.alert_received.emit(alert)

        def on_error(ws, error):
            if self._running:
                logger.debug("[TwitchRewardWorker] EventSub WebSocket error: %s", error)

        def on_close(ws, close_code, close_msg):
            pass

        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    "wss://eventsub.wss.twitch.tv/ws",
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                self._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                if self._running:
                    self.error_occurred.emit(str(e))
            
            if not self._running:
                break
            self.msleep(3000)

    def stop(self):
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
