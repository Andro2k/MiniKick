# backend\workers\rewards_worker.py

import logging
from PySide6.QtCore import QThread, Signal
from backend.providers import KickAPIClient

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
        self._processed_order = [] 

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
                oldest_id = self._processed_order.pop(0)
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

    def __init__(self, api_client: KickAPIClient, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Fetch_Rewards")
        self.api_client = api_client
        self._is_shutting_down = False

    def run(self):
        try:
            resp = self.api_client.fetch_channel_rewards()
            data = resp.get("data", [])
            rewards_list = [item["title"] for item in data if isinstance(item, dict) and "title" in item]
            rewards_map = {item["title"]: item for item in data if isinstance(item, dict) and "title" in item}
            self.rewards_fetched.emit(rewards_list, rewards_map)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CreateRewardWorker(QThread):
    reward_created = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client: KickAPIClient, payload: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Create_Reward")
        self.api_client = api_client
        self.payload = payload

    def run(self):
        try:
            resp = self.api_client.create_channel_reward(
                title=self.payload.get("title", ""),
                cost=self.payload.get("cost", 100),
                description=self.payload.get("description", ""),
                background_color=self.payload.get("background_color", "#00e701"),
                is_user_input_required=self.payload.get("is_user_input_required", False),
                should_redemptions_skip_request_queue=self.payload.get("should_redemptions_skip_request_queue", False)
            )
            reward_data = resp.get("data", {})
            self.reward_created.emit(reward_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class UpdateRewardWorker(QThread):
    reward_updated = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client: KickAPIClient, reward_id: str, payload: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Update_Reward")
        self.api_client = api_client
        self.reward_id = reward_id
        self.payload = payload

    def run(self):
        try:
            resp = self.api_client.update_channel_reward(self.reward_id, self.payload)
            reward_data = resp.get("data", {})
            self.reward_updated.emit(reward_data)
        except Exception as e:
            self.error_occurred.emit(str(e))
