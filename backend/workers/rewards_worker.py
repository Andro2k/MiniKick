# backend\workers\rewards_worker.py

import logging
from collections import deque
from PySide6.QtCore import QThread, Signal
from backend.providers.chat.kick_client import KickAPIClient

class RewardWorker(QThread):
    reward_redeemed = Signal(str, str, str)
    error_occurred = Signal(str)

    def __init__(self, i18n, api_client: KickAPIClient, poll_interval_seconds: int = 10, parent=None):
        super().__init__(parent) 
        self.i18n = i18n
        self.setObjectName("Worker_Reward_Polling") 
        self.api_client = api_client
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._processed_ids = set() 
        self._processed_order = deque() 

    def run(self):
        self._running = True
        
        while self._running:
            try:
                response = self.api_client.fetch_pending_redemptions()
                data_list = response.get("data", [])                           
                pending_redemptions = []
                user_ids_to_fetch = set()
                
                for item in data_list:
                    reward_title = item.get("reward", {}).get("title", self.i18n.get("main.workers.reward.unknown_reward"))
                    for red in item.get("redemptions", []):
                        red_id = red.get("id")
                        if red_id in self._processed_ids:
                            continue
                            
                        user_id = red.get("redeemer", {}).get("user_id")
                        user_input = red.get("user_input", "")
                        
                        if user_id:
                            user_ids_to_fetch.add(user_id)
                            
                        pending_redemptions.append({
                            "red_id": red_id,
                            "user_id": user_id,
                            "reward_title": reward_title,
                            "user_input": user_input
                        })
                if pending_redemptions:
                    self._process_and_emit_redemptions(pending_redemptions, list(user_ids_to_fetch))
                    
            except Exception as e:
                self.error_occurred.emit(self.i18n.get("main.workers.reward.poll_error").replace("{error}", str(e)))
            for _ in range(self.poll_interval * 10):
                if not self._running:
                    break
                self.msleep(100)

    def _process_and_emit_redemptions(self, redemptions: list, user_ids: list):
        user_names_map = {}
        new_ids_to_accept = []        
        if user_ids:
            try:
                users_response = self.api_client.get_users_by_ids(user_ids)
                for user_data in users_response.get("data", []):
                    user_names_map[user_data.get("user_id")] = user_data.get("name")
            except Exception as e:
                logging.error("[RewardWorker] Error hydrating reward users: %s", e)
        for red in redemptions:
            red_id = red["red_id"]
            user_id = red["user_id"]
            fallback_name = self.i18n.get("main.workers.reward.someone")
            username = user_names_map.get(user_id, str(user_id) if user_id else fallback_name)
            
            if len(self._processed_ids) >= 2000:
                oldest_id = self._processed_order.popleft()
                self._processed_ids.discard(oldest_id)
                
            self._processed_ids.add(red_id)
            self._processed_order.append(red_id)
            new_ids_to_accept.append(red_id)
            self.reward_redeemed.emit(username, red["reward_title"], red["user_input"])
        if new_ids_to_accept:
            for i in range(0, len(new_ids_to_accept), 25):
                batch = new_ids_to_accept[i:i+25]
                try:
                    self.api_client.accept_redemptions(batch)
                    logging.info("[RewardWorker] Successfully accepted batch of %d redemptions", len(batch))
                except Exception as api_err:
                    logging.error("[RewardWorker] Error accepting redemptions batch: %s", api_err)

    def stop(self):
        self._running = False

class FetchRewardsWorker(QThread):
    rewards_fetched = Signal(object, object)
    error_occurred = Signal(str)

    def __init__(self, api_client, broadcaster_id: str = "", platform: str = "kick", parent=None):
        super().__init__(parent)
        self.setObjectName(f"Worker_Fetch_Rewards_{platform}")
        self.api_client = api_client
        self.broadcaster_id = broadcaster_id
        self.platform = platform
        self._is_shutting_down = False

    def run(self):
        try:
            if self.platform == "twitch":
                resp = self.api_client.fetch_channel_rewards(self.broadcaster_id)
            else:
                resp = self.api_client.fetch_channel_rewards()

            data = resp.get("data", [])
            rewards_list = []
            rewards_map = {}
            for item in data:
                if isinstance(item, dict) and "title" in item:
                    title = item["title"]
                    item["platform"] = self.platform
                    rewards_list.append(title)
                    rewards_map[title] = item

            self.rewards_fetched.emit(rewards_list, rewards_map)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CreateRewardWorker(QThread):
    reward_created = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, payload: dict, broadcaster_id: str = "", platform: str = "kick", parent=None):
        super().__init__(parent)
        self.setObjectName(f"Worker_Create_Reward_{platform}")
        self.api_client = api_client
        self.payload = payload
        self.broadcaster_id = broadcaster_id
        self.platform = platform

    def run(self):
        try:
            if self.platform == "twitch":
                resp = self.api_client.create_channel_reward(
                    broadcaster_id=self.broadcaster_id,
                    title=self.payload.get("title", ""),
                    cost=self.payload.get("cost", 100),
                    description=self.payload.get("description", ""),
                    background_color=self.payload.get("background_color", "#9146FF"),
                    is_user_input_required=self.payload.get("is_user_input_required", False)
                )
            else:
                resp = self.api_client.create_channel_reward(
                    title=self.payload.get("title", ""),
                    cost=self.payload.get("cost", 100),
                    description=self.payload.get("description", ""),
                    background_color=self.payload.get("background_color", "#00e701"),
                    is_user_input_required=self.payload.get("is_user_input_required", False),
                    should_redemptions_skip_request_queue=self.payload.get("should_redemptions_skip_request_queue", False)
                )
            reward_data = resp.get("data", {})
            if isinstance(reward_data, dict):
                reward_data["platform"] = self.platform
            self.reward_created.emit(reward_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class UpdateRewardWorker(QThread):
    reward_updated = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, reward_id: str, payload: dict, broadcaster_id: str = "", platform: str = "kick", parent=None):
        super().__init__(parent)
        self.setObjectName(f"Worker_Update_Reward_{platform}")
        self.api_client = api_client
        self.reward_id = reward_id
        self.payload = payload
        self.broadcaster_id = broadcaster_id
        self.platform = platform

    def run(self):
        try:
            if self.platform == "twitch":
                resp = self.api_client.update_channel_reward(
                    broadcaster_id=self.broadcaster_id,
                    reward_id=self.reward_id,
                    payload=self.payload
                )
            else:
                resp = self.api_client.update_channel_reward(self.reward_id, self.payload)
            reward_data = resp.get("data", {})
            if isinstance(reward_data, dict):
                reward_data["platform"] = self.platform
            self.reward_updated.emit(reward_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class TwitchRewardWorker(QThread):
    reward_redeemed = Signal(str, str, str)
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
        import json
        import websocket
        import requests

        self._running = True

        def on_message(ws, msg_str):
            try:
                msg = json.loads(msg_str)
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
                    body = {
                        "type": "channel.channel_points_custom_reward_redemption.add",
                        "version": "1",
                        "condition": {"broadcaster_user_id": self.broadcaster_id},
                        "transport": {
                            "method": "websocket",
                            "session_id": session_id
                        }
                    }
                    try:
                        requests.post("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers, json=body, timeout=6)
                    except Exception as sub_err:
                        logging.warning("[TwitchRewardWorker] Error subscribing EventSub: %s", sub_err)

            elif msg_type == "notification":
                sub_type = metadata.get("subscription_type", "")
                if sub_type == "channel.channel_points_custom_reward_redemption.add":
                    event = payload.get("event", {})
                    user_name = event.get("user_name") or event.get("user_login") or "Anónimo"
                    reward_title = event.get("reward", {}).get("title", "")
                    user_input = event.get("user_input", "")
                    if reward_title:
                        self.reward_redeemed.emit(user_name, reward_title, user_input)

        def on_error(ws, error):
            if self._running:
                logging.debug("[TwitchRewardWorker] EventSub WebSocket error: %s", error)

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

